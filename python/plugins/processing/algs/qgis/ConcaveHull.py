# -*- coding: utf-8 -*-

"""
***************************************************************************
    ConcaveHull.py
    ---------------------
    Date                 : May 2014
    Copyright            : (C) 2012 by Piotr Pociask
    Email                : piotr dot pociask at gis-support dot pl
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
from builtins import range

__author__ = 'Piotr Pociask'
__date__ = 'May 2014'
__copyright__ = '(C) 2014, Piotr Pociask'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.core import (QgsFeatureRequest,
                       QgsFeature,
                       QgsGeometry,
                       QgsWkbTypes,
                       QgsApplication)
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
from processing.core.parameters import ParameterVector
from processing.core.parameters import ParameterNumber
from processing.core.parameters import ParameterBoolean
from processing.core.outputs import OutputVector
from processing.tools import dataobjects
import processing
from math import sqrt


class ConcaveHull(GeoAlgorithm):

    INPUT = 'INPUT'
    ALPHA = 'ALPHA'
    HOLES = 'HOLES'
    NO_MULTIGEOMETRY = 'NO_MULTIGEOMETRY'
    OUTPUT = 'OUTPUT'

    def icon(self):
        return QgsApplication.getThemeIcon("/providerQgis.svg")

    def svgIconPath(self):
        return QgsApplication.iconPath("providerQgis.svg")

    def group(self):
        return self.tr('Vector geometry tools')

    def name(self):
        return 'concavehull'

    def displayName(self):
        return self.tr('Concave hull')

    def defineCharacteristics(self):
        self.addParameter(ParameterVector(ConcaveHull.INPUT,
                                          self.tr('Input point layer'), [dataobjects.TYPE_VECTOR_POINT]))
        self.addParameter(ParameterNumber(self.ALPHA,
                                          self.tr('Threshold (0-1, where 1 is equivalent with Convex Hull)'),
                                          0, 1, 0.3))
        self.addParameter(ParameterBoolean(self.HOLES,
                                           self.tr('Allow holes'), True))
        self.addParameter(ParameterBoolean(self.NO_MULTIGEOMETRY,
                                           self.tr('Split multipart geometry into singleparts geometries'), False))
        self.addOutput(
            OutputVector(ConcaveHull.OUTPUT, self.tr('Concave hull'), datatype=[dataobjects.TYPE_VECTOR_POLYGON]))

    def processAlgorithm(self, feedback):
        layer = dataobjects.getLayerFromString(self.getParameterValue(ConcaveHull.INPUT))
        alpha = self.getParameterValue(self.ALPHA)
        holes = self.getParameterValue(self.HOLES)
        no_multigeom = self.getParameterValue(self.NO_MULTIGEOMETRY)

        # Delaunay triangulation from input point layer
        feedback.setProgressText(self.tr('Creating Delaunay triangles...'))
        delone_triangles = processing.run("qgis:delaunaytriangulation", layer, None)['OUTPUT']
        delaunay_layer = dataobjects.getLayerFromString(delone_triangles)

        # Get max edge length from Delaunay triangles
        feedback.setProgressText(self.tr('Computing edges max length...'))
        features = delaunay_layer.getFeatures()
        if len(features) == 0:
            raise GeoAlgorithmExecutionException(self.tr('No Delaunay triangles created.'))

        counter = 50. / len(features)
        lengths = []
        edges = {}
        for feat in features:
            line = feat.geometry().asPolygon()[0]
            for i in range(len(line) - 1):
                lengths.append(sqrt(line[i].sqrDist(line[i + 1])))
            edges[feat.id()] = max(lengths[-3:])
            feedback.setProgress(feat.id() * counter)
        max_length = max(lengths)

        # Get features with longest edge longer than alpha*max_length
        feedback.setProgressText(self.tr('Removing features...'))
        counter = 50. / len(edges)
        i = 0
        ids = []
        for id, max_len in list(edges.items()):
            if max_len > alpha * max_length:
                ids.append(id)
            feedback.setProgress(50 + i * counter)
            i += 1

        # Remove features
        delaunay_layer.selectByIds(ids)
        delaunay_layer.startEditing()
        delaunay_layer.deleteSelectedFeatures()
        delaunay_layer.commitChanges()

        # Dissolve all Delaunay triangles
        feedback.setProgressText(self.tr('Dissolving Delaunay triangles...'))
        dissolved = processing.run("qgis:dissolve", delaunay_layer,
                                   True, None, None)['OUTPUT']
        dissolved_layer = dataobjects.getLayerFromString(dissolved)

        # Save result
        feedback.setProgressText(self.tr('Saving data...'))
        feat = QgsFeature()
        dissolved_layer.getFeatures(QgsFeatureRequest().setFilterFid(0)).nextFeature(feat)
        writer = self.getOutputFromName(self.OUTPUT).getVectorWriter(
            layer.fields().toList(), QgsWkbTypes.Polygon, layer.crs())
        geom = feat.geometry()
        if no_multigeom and geom.isMultipart():
            # Only singlepart geometries are allowed
            geom_list = geom.asMultiPolygon()
            for single_geom_list in geom_list:
                single_feature = QgsFeature()
                single_geom = QgsGeometry.fromPolygon(single_geom_list)
                if not holes:
                    # Delete holes
                    deleted = True
                    while deleted:
                        deleted = single_geom.deleteRing(1)
                single_feature.setGeometry(single_geom)
                writer.addFeature(single_feature)
        else:
            # Multipart geometries are allowed
            if not holes:
                # Delete holes
                deleted = True
                while deleted:
                    deleted = geom.deleteRing(1)
            writer.addFeature(feat)
        del writer
