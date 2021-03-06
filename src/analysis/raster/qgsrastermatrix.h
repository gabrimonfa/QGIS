/***************************************************************************
                          qgsrastermatrix.h
                          -----------------
    begin                : 2010-10-23
    copyright            : (C) 20010 by Marco Hugentobler
    email                : marco dot hugentobler at sourcepole dot ch
***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

#ifndef QGSRASTERMATRIX_H
#define QGSRASTERMATRIX_H

#include "qgis_analysis.h"

/** \ingroup analysis
 * \class QgsRasterMatrix
 */
class ANALYSIS_EXPORT QgsRasterMatrix
{
  public:

    enum TwoArgOperator
    {
      opPLUS,
      opMINUS,
      opMUL,
      opDIV,
      opPOW,
      opEQ,         // =
      opNE,         // != resp. <>
      opGT,         // >
      opLT,         // <
      opGE,         // >=
      opLE,         // <=
      opAND,
      opOR
    };

    enum OneArgOperator
    {
      opSQRT,
      opSIN,
      opCOS,
      opTAN,
      opASIN,
      opACOS,
      opATAN,
      opSIGN,
      opLOG,
      opLOG10,
    };

    //! Takes ownership of data array
    QgsRasterMatrix();
    //! \note note available in Python bindings
    QgsRasterMatrix( int nCols, int nRows, double *data, double nodataValue );
    QgsRasterMatrix( const QgsRasterMatrix &m );
    ~QgsRasterMatrix();

    //! Returns true if matrix is 1x1 (=scalar number)
    bool isNumber() const { return ( mColumns == 1 && mRows == 1 ); }
    double number() const { return mData[0]; }

    //! Returns data array (but not ownership)
    //! \note not available in Python bindings
    double *data() { return mData; }
    //! Returns data and ownership. Sets data and nrows, ncols of this matrix to 0
    //! \note not available in Python bindings
    double *takeData();

    void setData( int cols, int rows, double *data, double nodataValue );

    int nColumns() const { return mColumns; }
    int nRows() const { return mRows; }

    double nodataValue() const { return mNodataValue; }
    void setNodataValue( double d ) { mNodataValue = d; }

    QgsRasterMatrix &operator=( const QgsRasterMatrix &m );
    //! Adds another matrix to this one
    bool add( const QgsRasterMatrix &other );
    //! Subtracts another matrix from this one
    bool subtract( const QgsRasterMatrix &other );
    bool multiply( const QgsRasterMatrix &other );
    bool divide( const QgsRasterMatrix &other );
    bool power( const QgsRasterMatrix &other );
    bool equal( const QgsRasterMatrix &other );
    bool notEqual( const QgsRasterMatrix &other );
    bool greaterThan( const QgsRasterMatrix &other );
    bool lesserThan( const QgsRasterMatrix &other );
    bool greaterEqual( const QgsRasterMatrix &other );
    bool lesserEqual( const QgsRasterMatrix &other );
    bool logicalAnd( const QgsRasterMatrix &other );
    bool logicalOr( const QgsRasterMatrix &other );

    bool squareRoot();
    bool sinus();
    bool asinus();
    bool cosinus();
    bool acosinus();
    bool tangens();
    bool atangens();
    bool changeSign();
    bool log();
    bool log10();

  private:
    int mColumns;
    int mRows;
    double *mData = nullptr;
    double mNodataValue;

    //! +,-,*,/,^,<,>,<=,>=,=,!=, and, or
    bool twoArgumentOperation( TwoArgOperator op, const QgsRasterMatrix &other );
    double calculateTwoArgumentOp( TwoArgOperator op, double arg1, double arg2 ) const;

    /*sqrt, sin, cos, tan, asin, acos, atan*/
    bool oneArgumentOperation( OneArgOperator op );
    bool testPowerValidity( double base, double power ) const;
};

#endif // QGSRASTERMATRIX_H
