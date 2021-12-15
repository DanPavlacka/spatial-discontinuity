# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                    QgsProcessingAlgorithm,
                    QgsProcessingParameterFeatureSource,
                    QgsProcessingParameterVectorDestination,
                    QgsProcessingParameterField,
                    QgsProcessingParameterString,
                    QgsProcessingParameterFileDestination              
                    )
from qgis import processing


class Discontinuity(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Discontinuity()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'discontinuity'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('discontinuity')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('scripts')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'scripts'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("Shows average discontinuity of an attribute along the border")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        ###input
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'INPUT',
                self.tr('Input vector layer'),
                [QgsProcessing.TypeVectorAnyGeometry]))
            
        ###dissolve field
        self.addParameter( 
            QgsProcessingParameterField(
                'dissolve_field',
                'Choose dissolve Field',
                '',
                parentLayerParameterName = 'INPUT'))

        ###fieldValue - hodnota která označuje jednotlivá přeshraniční území - vybraná bude ve výsledku kladná
        self.addParameter(
            QgsProcessingParameterString(
                'STAT', 
                self.tr('Insert one dissolve field attribute value'),
                None,
                False))
        # cílový atribut jako Y do grafu
        self.addParameter( 
            QgsProcessingParameterField(
                'y_field',
                'field to plot',
                '',
                parentLayerParameterName = 'INPUT'))

        #outputs          
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                'CALCULATOR_OUTPUT',
                self.tr('Calculator output')
            ))       

        self.addParameter(
            QgsProcessingParameterFileDestination(
                'R_OUTPUT',
                self.tr('Output plot'),
                '.html',
                None
            ))
        
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                'DISSOLVE_OUTPUT',
                self.tr('Dissolve output(optimal)')
            ))

        self.addParameter(
            QgsProcessingParameterVectorDestination(
                'EDGES_OUTPUT',
                self.tr('Edges output(optimal)')
            ))
            
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                'CENTROIDS_OUTPUT',
                self.tr('Centroids output(optimal)')
            ))   
            ##lines to points
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                'POINTS_OUTPUT',
                self.tr('Points output(optimal)')
            ))

        self.addParameter(
            QgsProcessingParameterVectorDestination(
                'DISTANCE_OUTPUT',
                self.tr('Distance output(optimal)')
            ))        




    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        input_featuresource = self.parameterAsSource(
            parameters,
            'INPUT',
            context)

        input_dissolveField = self.parameterAsString(
            parameters,
            'dissolve_field',
            context)

        input_stat = self.parameterAsString(
            parameters,
            'STAT', 
            context
        )        

        y_f = self.parameterAsString(
            parameters,
            'y_field',
            context)
        
        if feedback.isCanceled():
            return {}

        #########dissolve - potreba pred vytvorenim hranice
        dissolve_result = processing.run(
            'native:dissolve',{
                'INPUT':parameters['INPUT'], 
                'FIELD':parameters['dissolve_field'],
                'OUTPUT':parameters['DISSOLVE_OUTPUT']
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback
        )
        
        if feedback.isCanceled():
            return {}
        #########shared poly edges - vytvoreni hranice
        ###################potreba doresit shp
        sharedEdges_result = processing.run(
            'saga:sharedpolygonedges',{
                'POLYGONS':dissolve_result['OUTPUT'], 
                'ATTRIBUTE':parameters['dissolve_field'],
                'EPSILON':'0',
                'VERTICES':False, 
                'DOUBLE':False, 
                'EDGES':parameters['EDGES_OUTPUT']
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback
        )
        
        if feedback.isCanceled():
            return {}

        ###centroidy        
        centroids_result = processing.run(
            'native:centroids',{
                'INPUT':parameters['INPUT'],
                'ALL_PARTS':False, 
                'OUTPUT':parameters['CENTROIDS_OUTPUT']
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback
        )

        if feedback.isCanceled():
            return {}

        ###linie na body
        points_result = processing.run(
            'saga:convertlinestopoints',{
                'LINES':sharedEdges_result['EDGES'],
                'ADD         ':True, 
                'DIST':10,
                'POINTS':parameters['POINTS_OUTPUT']
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback
        )
        
        if feedback.isCanceled():
            return {}

        distance_result = processing.run(
            'qgis:distancetonearesthubpoints', {
                'INPUT':centroids_result['OUTPUT'], 
                'HUBS':points_result['POINTS'], 
                'FIELD':'ID_A', 
                'UNIT':3, 
                'OUTPUT':parameters['DISTANCE_OUTPUT']
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback
        )

        if feedback.isCanceled():
            return {}


        uzemi = parameters['STAT']
        fieldCalcForm = 'if(stat =\'' + uzemi + '\', HubDist,HubDist * (-1))'
        
        calculator_result = processing.run(
            'qgis:fieldcalculator', {
                'INPUT':distance_result['OUTPUT'], 
                'FIELD_NAME':'distance',
                'FIELD_TYPE':0,
                'FIELD_LENGTH':10,
                'FIELD_PRECISION':4,
                'NEW_FIELD':True,
                'FORMULA':fieldCalcForm,
                'OUTPUT':parameters['CALCULATOR_OUTPUT']
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback
        )

        if feedback.isCanceled():
            return {}

        ##pripojeni Rscriptu
        r_result = processing.run(
            'r:Discontinuity_R',{
                'Layer':calculator_result['OUTPUT'], 
                'X':'distance',
                'Y':parameters['y_field'],
                'col':parameters['dissolve_field'],
                'RPLOTS':parameters['R_OUTPUT']
            },
            is_child_algorithm=True,
            context=context,
            feedback=feedback
        )


        if feedback.isCanceled():
            return {}

        return {
            'DISSOLVE_OUTPUT': dissolve_result['OUTPUT'],
            'EDGES_OUTPUT': sharedEdges_result['EDGES'],
            'CENTROIDS_OUTPUT' : centroids_result['OUTPUT'],
            'POINTS_OUTPUT' : points_result['POINTS'],
            'DISTANCE_OUTPUT' : distance_result['OUTPUT'], 
            'CALCULATOR_OUTPUT' : calculator_result['OUTPUT'],
            'R_OUTPUT' : r_result['RPLOTS']
        }

