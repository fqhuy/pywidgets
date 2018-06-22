from PyQt5 import QtGui
from PyQt5.QtCore import (QByteArray, QDataStream, QFile, QFileInfo,
        QIODevice, QPoint, QPointF, QRectF, Qt, QRect, QSize, pyqtSignal, pyqtSlot)
from PyQt5.QtGui import (QColor, QBrush, QPixmap, QPainter, QBitmap, QIcon, QFont, QPen, QTransform, QPainterPath)
from PyQt5.QtWidgets import (QGraphicsScene, QGraphicsItem, QGraphicsTextItem, QGraphicsView)


class InteractiveView(QGraphicsView):
    # signals:
    # void pushScenes(QList < DesignScene * >);
    # void pushInitSniperView(QImage *);
    # void pushRecheckDesignActions();
    pushScenes = pyqtSignal(list)
    pushInitSniperView = pyqtSignal(QImage)
    pushRecheckDesignActions = pyqtSignal()

    def __init__(self):
        super(InteractiveView, self).__init__()

    # public slots:
    # void initScenes(QList < QImage * >);
    def initScenes(self, images):
        pass

    # void changeScene(qreal);
    def changeScene(self, value):
        pass

    # void zoomin(QPointF);
    # void setFlagZooming(bool);
    # void updateNodesAllScene(TrackerData3);
    # bool insertGlobalPtAllScene(int, int, float);
    # bool setClosedCurveAllScene(int);
    # bool setGlobalPtDeleteAllScene(int, int);
    # bool globalPtsDeleteAllScene();
    # bool checkPtsNumConsKeyframes(QList < int >);
    # int getNumAllPoints();
    # void checkClosedCurveAllScenes();
    # void resetRotationAllScenes();
    # void copyNodeListFromTo(int, int);
    # void updateRightClick(QPointF);
    # void dragView(QPointFc);
    # void setDragScene(bool);
    # void setPtsVisAllScenes();
    # void setPtsVisAllScenes(bool);
    #
    # // void smoothPts();
    # // void cuspPts();
    #

    # void setCurFlagSelect(bool checked){this->curScene->setFlagSelection(checked);}
    def setCurFlagSelect(self, checked):
        self.curScene.setFlagSelection(checked)

    # void setCurFlagMove(bool checked){this->curScene->setFlagMove(checked);}
    # void setCurFlagDelete(bool checked){this->curScene->setFlagDelete(checked);}
    # void setCurFlagDrag(bool checked){this->curScene->setFlagDragPts(checked);}
    # void setCurFlagSolverDrag(bool checked){this->curScene->setFlagSolverDragPts(checked);}
    # void setCurFlagCreate(bool checked){this->curScene->setFlagCreate(checked);}
    # void setCurFlagModify(bool checked){this->curScene->setFlagModPoint(checked);}
    # void setCurFlagPoly(bool checked){this->curScene->displayPoly(checked);}
    # void setCurFlagRotation(bool checked){this->curScene->setRotateMode(checked);}
    # QList < bool > getCurFlags();
    # void cleanCurScene();
