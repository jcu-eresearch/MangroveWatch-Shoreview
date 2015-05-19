from django.contrib.gis.db import models
from django.contrib.auth.models import User
from catamidb.models import Image, Deployment
from django.core.validators import MinValueValidator, MaxValueValidator
from projects.managers import AnnotationSchemesManager, AnnotationCodesManager


class AnnotationSchemes(models.Model):
    """
        Parent for annotation codes. Allows us to be able to handle multiple annotation systems/schemes.
    """

    objects = AnnotationSchemesManager()
    owner = models.ForeignKey(User, null=True)
    name = models.TextField()
    version = models.CharField(max_length=200)

    class Meta:
        unique_together = (('name', 'version'), )

    def natural_key(self):
        return self.name, self.version


class AnnotationCodes(models.Model):
    """The base annotation (CAAB) structure.

    This stores all the levels of the classifaction tree
    with parent filled in as appropriate.
    """

    objects = AnnotationCodesManager()
    annotation_scheme = models.ForeignKey('projects.AnnotationSchemes')
    caab_code = models.TextField(unique=True) # 8 numbers
    cpc_code = models.TextField(blank=True, null=True) # CPC Code file code
    point_colour = models.TextField(max_length=6, blank=True, null=True) # hex RGB colour
    code_name = models.TextField()
    description = models.TextField()
    category_name = models.TextField(blank=True, null=True)

    parent = models.ForeignKey(
            'projects.AnnotationCodes',
            blank=True,
            null=True
        )

    def natural_key(self):
        return self.annotation_scheme.natural_key(), self.caab_code

    natural_key.dependencies = ['projects.AnnotationSchemes']

    class Meta:
        unique_together = (('annotation_scheme', 'caab_code'), )

    def __unicode__(self):
        return "{0} - ({1})".format(self.code_name, self.caab_code)


class QualifierCodes(models.Model):
    """Qualifiers to annotations.

    Examples include anthropogenic labels, or natural labels
    that include bleaching, dead etc.
    """

    annotation_scheme = models.ForeignKey('projects.AnnotationSchemes')
    parent = models.ForeignKey('self', blank=True, null=True, related_name="children")
    short_name = models.CharField(max_length=200)
    description = models.CharField(max_length=200)

    #active - should this be displayed to the users
    #in case you want to keep the label for historical purposes,
    # but not display it to the users
    active = models.BooleanField()


class Project(models.Model):
    """
    Projects contain a set of images that a user works with. They also have
    associated worksets which are image sets to annotate.
    """

    PROJECT_TYPES = (
        ('CATAMI', 'CATAMI Classification'),
        ('Mangrove', 'Mangrove Classification'),
        ('Custom', 'Custom Classification Scheme'),
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(User, null=True)
    creation_date = models.DateTimeField()
    modified_date = models.DateTimeField()
    images = models.ManyToManyField(Image, null=True)
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPES)

    class Meta:
        unique_together = (('owner', 'name', 'creation_date'), )
        permissions = (
            ('view_project', 'View the project.'),
        )


class AnnotationSet(models.Model):
    """
    An annotated set is used to contain a set of images to be annotated.
    """

    IMAGE_SAMPLING_METHODOLOGY_CHOICES = (
        (0, 'Random'),
        (1, 'Stratified'),
        (2, 'Spatial'),
        (3, 'All'),
    )

    POINT_SAMPLING_METHODOLOGY_CHOICES = (
        (-1, 'Not Applicable'),
        (0, 'Random Point'),
        (1, 'Stratified Point'),
        (2, 'Fixed 5 Point'),
        (3, 'Uniform Grid'),
    )

    ANNOTATATION_SET_TYPE_CHOICES = (
        (0, 'Point'),
        (1, 'Whole Image'),
    )

    project = models.ForeignKey('projects.Project')
    owner = models.ForeignKey(User, null=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    creation_date = models.DateTimeField()
    modified_date = models.DateTimeField()
    images = models.ManyToManyField(Image, related_name='projects')
    image_sampling_methodology = models.IntegerField(choices=IMAGE_SAMPLING_METHODOLOGY_CHOICES)
    point_sampling_methodology = models.IntegerField(choices=POINT_SAMPLING_METHODOLOGY_CHOICES)
    annotation_set_type = models.IntegerField(choices=ANNOTATATION_SET_TYPE_CHOICES)

    class Meta:
        unique_together = (('owner', 'name', 'creation_date'), )
        permissions = (
            ('view_annotationset', 'View the  annotation set.'),
        )


class Annotation(models.Model):
    """The common base for Point and Whole image annotations.
    """

    image = models.ForeignKey('catamidb.Image')
    owner = models.ForeignKey(User, null=True)

    #loose reference to AnnotationCode table
    annotation_caab_code = models.CharField(max_length=200)

    #loose reference to qualifier table
    qualifier_short_name = models.CharField(max_length=200)

    #secondary annotation code and qualifier 
    annotation_caab_code_secondary = models.CharField(max_length=200, blank=True)
    qualifier_short_name_secondary = models.CharField(max_length=200, blank=True)

    class Meta:
        """Defines Metaparameters of the model."""
        abstract = True


class PointAnnotation(Annotation):
    """
    A Point annotation.

    Contains position within the image (as a percent from top left) and
    the set to which it belongs.
    """

    annotation_set = models.ForeignKey('projects.AnnotationSet')

    x = models.FloatField(validators = [MinValueValidator(0.0), MaxValueValidator(100.0)])
    y = models.FloatField(validators = [MinValueValidator(0.0), MaxValueValidator(100.0)])


class WholeImageAnnotation(Annotation):
    """
    A Whole Image annotation.

    Needed to distinguish the difference between point and whole image
    annotation.
    """

    annotation_set = models.ForeignKey('projects.AnnotationSet')

    # -1 signifies that no percentage cover has been given
    coverage_percentage = models.IntegerField(validators = [MinValueValidator(-1), MaxValueValidator(100)], default = -1)
