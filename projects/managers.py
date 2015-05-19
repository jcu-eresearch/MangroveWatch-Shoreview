import math
from django.db import transaction
import random
from django.contrib.gis.db import models
import numpy as np
import projects.authorization as project_authorization


class AnnotationSchemesManager(models.Manager):
    def get_by_natural_key(self, name, version):
        return self.get(name=name, version=version)


class AnnotationCodesManager(models.Manager):
    def get_by_natural_key(self, annotation_scheme, caab_code):
        """

        :param annotation_scheme:
        :param caab_code:
        :return:

        This is a slightly complicated natural key selection, as we also need to get the natural key of the the parent annotaiton
        scheme. Assuming the fixture gets loaded as follows ["name", "version"] for the annotation scheme.

        """

        from projects.models import AnnotationSchemes
        print annotation_scheme, caab_code
        return self.get(annotation_scheme=AnnotationSchemes.objects.get_by_natural_key(annotation_scheme[0], annotation_scheme[1]), caab_code=caab_code)


class PointAnnotationManager(models.Manager):
    """ Handles logic functions related to points annotations """

    def apply_random_sampled_points(self, annotation_set, sample_size):
        """ Randomly apply points to the images attached to this annotation
            set """

        from projects.models import PointAnnotation

        images = annotation_set.images.all()
        points_to_bulk_save = []

        # iterate through the images and create points
        for image in images:
            for i in range(int(sample_size)):

                point_annotation = PointAnnotation()

                point_annotation.annotation_set = annotation_set
                point_annotation.image = image
                point_annotation.owner = annotation_set.owner
                point_annotation.x = random.uniform(0.008, 0.992) #random.random()
                point_annotation.y = random.uniform(0.008, 0.992)

                point_annotation.annotation_caab_code = ""
                point_annotation.qualifier_short_name = ""

                point_annotation.annotation_caab_code_secondary = ""
                point_annotation.qualifier_short_name_secondary = ""

                #point_annotation.save()
                points_to_bulk_save.append(point_annotation)

        # do the bulk save - for performance
        PointAnnotation.objects.bulk_create(points_to_bulk_save)

    def import_sampled_points(self, annotation_set, import_data):
        """ create annotation points with information from uploaded CSV and add to this annotation
            set """

        from projects.models import PointAnnotation

        images = annotation_set.images.all()
        points_to_bulk_save = []

        # iterate through the images and create points
        for image in images:
            for annotation in import_data[str(image.deployment.id)][image.image_name]:

                point_annotation = PointAnnotation()
                point_annotation.annotation_set = annotation_set
                point_annotation.image = image
                point_annotation.owner = annotation_set.owner
                point_annotation.x = annotation['Point in Image'].split(',')[0]
                point_annotation.y = annotation['Point in Image'].split(',')[1]

                point_annotation.annotation_caab_code = annotation['Annotation Code']
                point_annotation.qualifier_short_name = annotation['Qualifier Name']

                point_annotation.annotation_caab_code_secondary = annotation['Annotation Code 2']
                point_annotation.qualifier_short_name_secondary = annotation['Qualifier Name 2']

                #point_annotation.save()
                points_to_bulk_save.append(point_annotation)

        # do the bulk save - for performance
        PointAnnotation.objects.bulk_create(points_to_bulk_save)

    def apply_stratified_sampled_points(self, annotation_set, sample_size):
        """ Apply points to the images attached to this annotation set using
            stratified sampling """

        #TODO: implement
        return None

    def apply_uniform_grid_points(self, annotation_set, sample_size):
        """ Apply a uniform grid of points to an image. """

        from projects.models import PointAnnotation

        images = annotation_set.images.all()
        points_to_bulk_save = []

        # take the square root of the sample size and round
        square = math.sqrt(int(sample_size))
        rows = columns = round(square)

        # +1 to the rows and cols
        rows += 1
        columns += 1

        # create the grid
        row_points = np.linspace(0.008, 0.992, num=rows, endpoint=False)
        column_points = np.linspace(0.008, 0.992, num=columns, endpoint=False)

        # pop the first item from the arrays - we do this so we get an even spacing excluding edges
        row_points = np.delete(row_points, 0)
        column_points = np.delete(column_points, 0)

        # apply the points to the images
        for image in images:
            for row in row_points:
                for column in column_points:

                    point_annotation = PointAnnotation()

                    point_annotation.annotation_set = annotation_set
                    point_annotation.image = image
                    point_annotation.owner = annotation_set.owner
                    point_annotation.x = row
                    point_annotation.y = column

                    point_annotation.annotation_caab_code = ""
                    point_annotation.qualifier_short_name = ""

                    point_annotation.annotation_caab_code_secondary = ""
                    point_annotation.qualifier_short_name_secondary = ""

                    #point_annotation.save()
                    points_to_bulk_save.append(point_annotation)

        # do the bulk save - for performance
        PointAnnotation.objects.bulk_create(points_to_bulk_save)

    def apply_fixed_five_points(self, annotation_set):
        """ 5 points based on AIMS standard """

        from projects.models import PointAnnotation

        images = annotation_set.images.all()
        points_to_bulk_save = []

        # create the grid
        row_points = [0.25, 0.25, 0.5, 0.75, 0.75]
        column_points = [0.25, 0.75, 0.5, 0.75, 0.25]

        # apply the points to the images
        for image in images:
            for i in range(int(5)):
                    point_annotation = PointAnnotation()

                    point_annotation.annotation_set = annotation_set
                    point_annotation.image = image
                    point_annotation.owner = annotation_set.owner
                    point_annotation.x = row_points[i]
                    point_annotation.y = column_points[i]

                    point_annotation.annotation_caab_code = ""
                    point_annotation.qualifier_short_name = ""

                    point_annotation.annotation_caab_code_secondary = ""
                    point_annotation.qualifier_short_name_secondary = ""

                    #point_annotation.save()
                    points_to_bulk_save.append(point_annotation)

        # do the bulk save - for performance
        PointAnnotation.objects.bulk_create(points_to_bulk_save)


class WholeImageAnnotationManager(models.Manager):
    """ Handles logic functions related to whole image annotations """

    def apply_whole_image_points(self, annotation_set):
        """ Randomly apply points to the images attached to this annotation
            set """

        from projects.models import WholeImageAnnotation

        whole_image_annotation_count = 4
        images = annotation_set.images.all()
        points_to_bulk_save = []

        # iterate through the images and create points

        for image in images:
            for i in range(whole_image_annotation_count):
                whole_image_annotation = WholeImageAnnotation()

                whole_image_annotation.annotation_set = annotation_set
                whole_image_annotation.image = image
                whole_image_annotation.owner = annotation_set.owner

                whole_image_annotation.annotation_caab_code = ""
                whole_image_annotation.qualifier_short_name = ""

                whole_image_annotation.annotation_caab_code_secondary = ""
                whole_image_annotation.qualifier_short_name_secondary = ""

                points_to_bulk_save.append(whole_image_annotation)

        # do the bulk save - for performance
        WholeImageAnnotation.objects.bulk_create(points_to_bulk_save)

    def import_whole_image_points(self,annotation_set, import_data):
        """ create annotation points with information from uploaded CSV and add to this annotation
            set """

        from projects.models import WholeImageAnnotation

        images = annotation_set.images.all()
        points_to_bulk_save = []

        # iterate through the images and create points
        for image in images:
            for annotation in import_data[str(image.deployment.id)][image.image_name]:
                whole_image_annotation = WholeImageAnnotation()

                whole_image_annotation.annotation_set = annotation_set
                whole_image_annotation.image = image
                whole_image_annotation.owner = annotation_set.owner

                whole_image_annotation.annotation_caab_code = annotation['Annotation Code']
                whole_image_annotation.qualifier_short_name = ['Qualifier Name']

                whole_image_annotation.annotation_caab_code_secondary = annotation['Annotation Code']
                whole_image_annotation.qualifier_short_name_secondary = ['Qualifier Name 2']

                points_to_bulk_save.append(whole_image_annotation)

        # do the bulk save - for performance
        WholeImageAnnotation.objects.bulk_create(points_to_bulk_save)

    @transaction.commit_on_success
    def copy_annotations_to_image(self, annotation_set_id, source_image_id, destination_image_id):
        """
        Copies whole image annotations from one image to another
        """

        from projects.models import WholeImageAnnotation

        # get whole image annotations for the source image
        source_image_annotations = WholeImageAnnotation.objects.filter(annotation_set=annotation_set_id,
                                                                       image=source_image_id)

        # get whole image annotations for the destination image
        destination_image_annotations = WholeImageAnnotation.objects.filter(annotation_set=annotation_set_id,
                                                                            image=destination_image_id)

        # delete the annotations from destination
        for annotation in destination_image_annotations:
            annotation.delete()

        # copy annotations from source
        for annotation in source_image_annotations:
            WholeImageAnnotation(annotation_set_id=annotation_set_id,
                                    image_id=destination_image_id,
                                    annotation_caab_code=annotation.annotation_caab_code,
                                    qualifier_short_name=annotation.qualifier_short_name,
                                    coverage_percentage=annotation.coverage_percentage).save()

    def check_if_images_have_same_annotations(self, annotation_set_id, image_one, image_two):

        from projects.models import WholeImageAnnotation

        # get whole image annotations for the source image
        image_one_annotations = WholeImageAnnotation.objects.filter(annotation_set=annotation_set_id,
                                                                    image=image_one)

        # get whole image annotations for the destination image
        image_two_annotations = WholeImageAnnotation.objects.filter(annotation_set=annotation_set_id,
                                                                    image=image_two)

        results_one = image_one_annotations.filter(annotation_caab_code="")
        results_two = image_two_annotations.filter(annotation_caab_code="")

        # if there are no annoatations on either, then not the same
        if (image_one_annotations.count() or image_two_annotations.count()) == 0:
            return "false"

        if results_one.count() == image_one_annotations.count():
            return "false"

        if results_two.count() == image_two_annotations.count():
            return "false"

        #if sizes are different, then they are not the same
        if image_one_annotations.count() != image_two_annotations.count():
            return "false"

        # loop through and check if A and B have the same contents
        for annotation in image_one_annotations:
            results = image_two_annotations.filter(annotation_caab_code=annotation.annotation_caab_code,
                                                   coverage_percentage=annotation.coverage_percentage)

            # no ? then these lists are not the same
            if results.count() == 0:
                return "false"

        return "true"

    def mangrove_copy_annotations_to_image(self, annotation_set_id, source_image_id, destination_image_id):
        """

        This is a special function for the mangrove watch workflow. Rather than deleting all annotations on the
        next image the copy annotations to, they would like only annotations carried across for categories which
        have not been annotated on the next image.

        :param annotation_set_id:
        :param source_image_id:
        :param destination_image_id:
        :return:
        """

        from projects.models import WholeImageAnnotation, AnnotationCodes, Project, AnnotationSet

        # get whole image annotations for the source image
        source_image_annotations = WholeImageAnnotation.objects.filter(annotation_set=annotation_set_id,
                                                                       image=source_image_id)

        # get whole image annotations for the destination image
        destination_image_annotations = WholeImageAnnotation.objects.filter(annotation_set=annotation_set_id,
                                                                            image=destination_image_id).distinct()

        # get the destination image annotation categories
        categories_to_ignore = AnnotationCodes.objects.filter(caab_code__in=destination_image_annotations.values_list("annotation_caab_code")).distinct()
        categories_to_ignore = categories_to_ignore.values_list('category_name', flat=True)

        # get the codes which lie in the category, so we can ignore them
        annotations_to_ignore = AnnotationCodes.objects.filter(category_name__in=categories_to_ignore).distinct()
        annotations_to_ignore = annotations_to_ignore.values_list("caab_code", flat=True)

        # get benthobot user
        benthobot_user = project_authorization.get_bentho_bot_user()
        project_authorization.apply_annotation_set_permissions(benthobot_user, AnnotationSet.objects.get(id=annotation_set_id))

        # copy annotations from source
        for annotation in source_image_annotations:
            if not (annotation.annotation_caab_code in annotations_to_ignore):
                WholeImageAnnotation(annotation_set_id=annotation_set_id,
                                    image_id=destination_image_id,
                                    annotation_caab_code=annotation.annotation_caab_code,
                                    qualifier_short_name=annotation.qualifier_short_name,
                                    coverage_percentage=annotation.coverage_percentage,
                                    owner=benthobot_user).save()

