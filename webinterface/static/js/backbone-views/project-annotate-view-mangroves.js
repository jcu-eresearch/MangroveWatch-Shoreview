var GlobalEvent = _.extend({}, Backbone.Events);

var QualifierCode = Backbone.Model.extend({
    urlRoot: "/api/dev/qualifier_code/",
    url: function() {
        var origUrl = Backbone.Model.prototype.url.call(this);
        return origUrl + (origUrl.charAt(origUrl.length - 1) == '/' ? '' : '/');
    }
});

var AnnotationScheme = Backbone.Model.extend({
    urlRoot: "/api/dev/annotation_scheme/",
    url: function() {
        var origUrl = Backbone.Model.prototype.url.call(this);
        return origUrl + (origUrl.charAt(origUrl.length - 1) == '/' ? '' : '/');
    }
});

var AnnotationSchemeList = Backbone.Tastypie.Collection.extend({
    urlRoot: "/api/dev/annotation_scheme/",
    model: AnnotationScheme
});

var AnnotationCode = Backbone.Model.extend({
    urlRoot: "/api/dev/annotation_code/",
    url: function() {
        var origUrl = Backbone.Model.prototype.url.call(this);
        return origUrl + (origUrl.charAt(origUrl.length - 1) == '/' ? '' : '/');
    }
});

var AnnotationCodeList = Backbone.Tastypie.Collection.extend({
    urlRoot: "/api/dev/annotation_code/",
    model: AnnotationCode
});

var BackboneImage = Backbone.Model.extend({
    urlRoot: "/api/dev/image",
    url: function() {
        var origUrl = Backbone.Model.prototype.url.call(this);
        return origUrl + (origUrl.charAt(origUrl.length - 1) == '/' ? '' : '/');
    }
});

var Images = Backbone.Tastypie.Collection.extend({
    model: BackboneImage,
    url: function(){
        return this.instanceUrl;
    },
    initialize: function(props){
        this.instanceUrl = props.url;
    }
});

var getBroadScaleClassificationCopyURL = function(annotationSetId) {
    return "/api/dev/annotation_set/" + annotationSetId + "/mangrove_copy_wholeimage_classification/"
}

var getBroadScaleSimilarityStatusURL = function(annotationSetId) {
    return "/api/dev/annotation_set/" + annotationSetId + "/get_image_similarity_status/"
}

var similarImages;
var thumbnailImages;
var thumbnailsPerPage = 20;
var points = new PointAnnotations();
var broadScalePoints = new WholeImageAnnotations();
var annotationSets = new AnnotationSets();
var annotationCodeList = new AnnotationCodeList();
var annotationSchemes = new AnnotationSchemeList();
var currentImageInView;
var map;
var bidResult;
var selectedImageId = -1;
var projectId = -1;
var selectedThumbnailPosition = 0;

//yeah, it's a global.
//var nested_annotation_list;
//var plain_annotation_list;

OrchestratorView = Backbone.View.extend({
    el: $('div'),
    events: {
        "click #configure_project_button": "doConfigure"
    },
    onLoadError: function(model, response, options) {
        if(response.status == 401) {
            $("#load-error-message").html("You do not have permission to view this project.");
        }
        else {
            $("#load-error-message").html("An error occurred trying to load this project. Try refreshing the page.");
        }

        $("#load-error-div").show();
    },
    initialize: function () {

        //look out for window resize events
        $(window).resize(function(e){
            //trigger an event to redraw
            GlobalEvent.trigger("screen_changed");
        });

        //load the data
        annotationSets.fetch({async:false, data: { project: projectId }, error: this.onLoadError});
        project.fetch({async: false, error: this.onLoadError, success: function() {
            this.imageMapView = new ImageMapView();
        }});
        //annotationCodeList.fetch({async: false, data: {limit: 500}});
        annotationSchemes.fetch({async: false});
        annotationCodeList.fetch({
            async: false,
            data: { limit: 999 },
            success: function (model, response, options) {
                //nested_annotation_list = classificationTreeBuilder(model.toJSON());
                //plain_annotation_list = model.toJSON();
                projectId = project.id;
            },
            error: this.onLoadError
        });

        var ann_id = annotationSets.at(0).get('id')

        var bookmarkedImageId = -1;
        var bid = catami_getURLParameter("bid"); //get image id from bid param from URL
        var fetchOffset = 0;        
        if (bid && bid != 'null') bookmarkedImageId = bid;

        if (bookmarkedImageId != -1) { //if there's an image id, get position of image within the annotation set
            jQuery.ajax({
                url: '/api/dev/annotation_set/'
                        + ann_id + '/'
                        + bookmarkedImageId
                        + '/image_by_id/',
                success: function (result) {
                    bidResult = result;
                    selectedImageId = result.imageId;
                    fetchOffset = Math.floor(result.position / thumbnailsPerPage) * thumbnailsPerPage;                    
                },
                async: false
            });            
        }

        similarImages = new Images({ "url": "/api/dev/annotation_set/" + ann_id + "/similar_images/" });
        thumbnailImages = new Images({ "url": "/api/dev/annotation_set/" + ann_id + "/images/?limit=" + thumbnailsPerPage });
        //fetchThumbnails(fetchOffset);
        //createPagination(thumbnailImages.meta);

        //load the views
        this.breadcrumbNavigationView = new BreadcrumbNavigationView({});
        this.thumbnailPaginationView = new ThumbanailPaginationView({});
        this.thumbnailStripView = new ThumbnailStripView({model : annotationSets});
        this.thumbnailStripView.loadThumbnails(fetchOffset);

        //this.imagesAnnotateView = new ImageAnnotateView({ model: annotationSets });

        //----
        this.imageCanvasView = new ImageCanvasView({ model: annotationSets });
        this.imageToolbarView = new ImageToolbarView({});
        //---

        //this.chooseAnnotationView = new ChooseAnnotationView({});

        if (annotationSets.at(0).get('annotation_set_type') === 1){
            //this.wholeImageAnnotationSelectorView = new WholeImageAnnotationSelectorView({});
            //this.wholeImageControlBarView = new WholeImageControlBarView({});
            //this.similarityImageView = new SimilarityImageView({});
            this.broadScaleAnnotationView = new BroadScaleAnnotationView({imageCanvasView: this.imageCanvasView});
            this.annotationSelectionView = new AnnotationSelectionView({broadScaleProject: true});
        } else {
            //hide similarity for point view
            $('#SimilarImageTabButton').hide();
            //this.pointControlBarView = new PointControlBarView({});
            this.pointAnnotationView = new PointAnnotationView({imageCanvasView: this.imageCanvasView});
            this.annotationSelectionView = new AnnotationSelectionView({broadScaleProject: false});
        }

        this.annotationStatusView = new AnnotationStatusView({});


        //render the views
        this.render();
    },
    render: function () {
        var image = thumbnailImages.first();
        selectedImageId = image.get('id');

        this.assign(this.breadcrumbNavigationView,'#BreadcrumbContainer');
        this.assign(this.thumbnailPaginationView, '#ContentContainer');
        this.assign(this.thumbnailStripView, '#ThumbnailStripContainer');

        //this.assign(this.imagesAnnotateView, '#ImageContainer');
        //this.assign(this.chooseAnnotationView, '#ChooseAnnotationContainer');
        this.assign(this.annotationStatusView, '#AnnotationStatusContainer');

        // broad scale classificaiton project
        if (annotationSets.at(0).get('annotation_set_type') === 1){
            //this.assign(this.wholeImageAnnotationSelectorView, '#whole-image-annotation-selector');
            //this.assign(this.similarityImageView, '#ImageSimilarityContainer');
            //this.assign(this.wholeImageControlBarView, '#ControlBarContainer');
            this.assign(this.annotationSelectionView, '#AnnotationSelectionTab');
        // fine scale classification project
        } else {
            //this.assign(this.pointControlBarView, '#ControlBarContainer');
            this.assign(this.annotationSelectionView, '#AnnotationSelectionTab');
        }

        var web_location = image.get('web_location');        
        
        if (bidResult) {
            selectedImageId = bidResult.imageId;
            web_location = bidResult.web_location
            bidResult = null;//reset
        }

        GlobalEvent.trigger("thumbnail_selected_by_id", selectedImageId, web_location);

    },
    assign : function (view, selector) {
        view.setElement($(selector)).render();
    },
    doConfigure: function (event) {
        //redirect to configuration page
        window.location.replace("/projects/" + project.get("id") + "/configure");
    }
});

/*
function loadPage(offset) {
    fetchThumbnails(offset);
    orchestratorView.thumbnailStripView.render();

    var image = thumbnailImages.first();
    selectedImageId = image.get('id');
    GlobalEvent.trigger("thumbnail_selected_by_id", selectedImageId, image.get('web_location'));
    GlobalEvent.trigger("annotation_set_has_changed"); //XXX triggering this event to fetch new image stats and redraw chart for image progress
}

function fetchThumbnails(offset) {
    var off = {};
    if (offset) off = offset;
    thumbnailImages.fetch({
        data: {
            offset: off
        },
        async: false,
        success: function (model, response, options) {
            currentOffset = offset;
            //alert('currentOffset : ' + currentOffset + ' after fetching meta : ' + thumbnailImages.meta.toSource());
        },
        error: function (model, response, options) {
            alert('Error fetching thumbnails : ' + response);
        }
    });
}*/

ThumbanailPaginationView = Backbone.View.extend({
    el: $('div'),
    initialize: function () {
        var parent = this;

        GlobalEvent.on("thumbnail_page_back", this.backClicked, this);
        GlobalEvent.on("thumbnail_page_forward", this.nextClicked, this);
        GlobalEvent.on("broad_scale_annotation_added", this.updateAnnotation, this);
        GlobalEvent.on("annotation_set_has_changed", this.updateAnnotation, this);

        $("#ThumbnailBackButton").click(function(event) {
            parent.backClicked(event);
        });

        $("#ThumbnailForwardButton").click(function(event) {
            parent.nextClicked(event);
        });

        $("#ThumbnailPageSelect").change(function(event) {
            parent.pageChanged(event);
        });

        $("#ThumbnailFilterSelect").change(function(event) {
            parent.filterChanged(event);
        });

        //load the filters
        this.updateAnnotation();

        this.render();
    },
    render: function() {
        var meta = thumbnailImages.meta;

        var limit = meta['limit'];
        var offset = meta['offset'];
        var total = meta['total_count'];
        //var next = meta['next'];
        //var prev = meta['previous'];
        var currentPage = 1 + Math.floor(offset / limit) + ((offset % limit == 0) ? 0 : 1);
        var maxPage = Math.floor(total / limit) + ((total % limit == 0) ? 0 : 1);

        for (var i=1; i<maxPage+1; i++) {
            $('#ThumbnailPageSelect')
                 .append($("<option></option>")
                 .attr("value",i)
                 .text(i));
        }

        this.limit = limit;

        //set the selected page
        $("#ThumbnailPageSelect").val(parseInt(currentPage));
    },
    backClicked: function(event) {
        var currentPage = $("#ThumbnailPageSelect").val();
        $("#ThumbnailPageSelect").val(parseInt(currentPage) - 1);

        var page = $("#ThumbnailPageSelect").val();

        this.loadPage(page);

        if(currentPage != page)
            this.selectLast();
        else
            this.selectFirst();
    },
    nextClicked: function(event) {
        var currentPage = $("#ThumbnailPageSelect").val();
        $("#ThumbnailPageSelect").val(parseInt(currentPage) + 1);

        var page = $("#ThumbnailPageSelect").val();

        this.loadPage(page);

        if(currentPage != page)
            this.selectFirst();
        else
            this.selectLast();
    },
    pageChanged: function(event) {

        // get the selected page
        var selectedPage = $(event.target).val();

        this.loadPage(parseInt(selectedPage));
        this.selectFirst();
    },
    filterChanged: function(event) {

        // get the selected category
        var selectedCategory = $(event.target).val();

        this.loadPage(parseInt(1));
        this.selectFirst();
    },
    getSelectedFilter: function() {
        return $('#ThumbnailFilterSelect').val();
    },
    loadPage: function(page) {

        var image_ids = this.getSelectedFilter();

        var offset = this.limit * (page - 1);
        orchestratorView.thumbnailStripView.loadThumbnails(offset, image_ids);
        orchestratorView.thumbnailStripView.render();
    },
    updateAnnotation: function () {
        //TODO: dangerous! remove this hack
        var ann_id = annotationSets.at(0).get('id');

        jQuery.ajax({
            url: '/api/dev/annotation_set/'
                    + ann_id + '/'
                    + 'mangrove_image_filters',
            success: function (result) {

                //update filter dropdown
                var selectedItem = $("#ThumbnailFilterSelect")[0].selectedIndex;

                if (selectedItem == -1)
                    selectedItem = 0;

                $('#ThumbnailFilterSelect')
                        .find('option')
                        .remove();

                $('#ThumbnailFilterSelect')
                         .append($("<option></option>")
                         .attr("value",null)
                         .text("All"));

                for (var i=0; i<result.length; i++) {
                    $('#ThumbnailFilterSelect')
                         .append($("<option></option>")
                         .attr("value", result[i].image_ids)
                         //.text("No " + result[i].category));
                         .text("(" + result[i].count + " images) " + "No " + result[i].category));
                }

                $("#ThumbnailFilterSelect")[0].selectedIndex = selectedItem;

            },
            error: function (model, response, options) {
                $.notify({
                    title: 'Failed to load thumbanil filter options.',
                    text: response.status,
                    type: 'error', // success | info | error
                    hide: true,
                    icon: false,
                    history: false,
                    sticker: false
                });
            },
            async: false
        });
    },
    selectFirst: function() {
        var image = thumbnailImages.first();
        selectedImageId = image.get('id');
        GlobalEvent.trigger("thumbnail_selected_by_id", selectedImageId, image.get('web_location'));
        GlobalEvent.trigger("annotation_set_has_changed");
    },
    selectLast: function() {
        var image = thumbnailImages.last();
        selectedImageId = image.get('id');
        GlobalEvent.trigger("thumbnail_selected_by_id", selectedImageId, image.get('web_location'));
        GlobalEvent.trigger("annotation_set_has_changed");
    },
    events: {}
});

ImageMapView = Backbone.View.extend({
    el: $('div'),
    initialize: function () {
        GlobalEvent.on("thumbnail_selected_by_id", this.updateMap, this);

        this.render();
    },
    render: function(){
        var mapExtent = project.get("map_extent");
        this.map = new NewProjectsMap(WMS_URL, LAYER_PROJECTS, 'map', mapExtent);
        //map.updateMapForSelectedProject(projectId);
        //map.updateMapForSelectedAnnotationSet(annotationSetId);
        //this.map.addImageLayer(50, WMS_URL, LAYER_IMAGES);
        this.map.zoomToExtent();
    },
    updateMap: function(imageId) {
        //this.map.clearMap();
        this.map.addOrUpdateImageLayer(imageId, WMS_URL, LAYER_IMAGES);
        //this.map.updateImage(imageId);
        this.map.zoomToExtent();
    },
    events: {}
});

BreadcrumbNavigationView = Backbone.View.extend({
    el: $('div'),
    initialize: function () {
    },
    render: function(){
        var annotationSetVariables = {
            "name": project.get("name"),
            "id": project.get("id")
        };

        // Compile the template using underscore
        var breadcrumbTemplate = _.template($("#BreadcrumbTemplate").html(), annotationSetVariables);

        // Load the compiled HTML into the Backbone "el"
        this.$el.html(breadcrumbTemplate);

        return this;
    },
    events: {}
});

var PointUtil = {
    /**
     * Returns a point object based on a given id
     * @param pointId
     * @returns {*}
     */
    getPointWithId: function(pointId) {
        // get the point from the collection
        var point = points.find(function(model) {
            return model.get('id') == pointId;
        });

        return point;
    },
    /**
     * Returns an AnnotationCode object for the primary annotation of a given point
     * @param pointId
     * @returns {*}
     */
    getAnnotationCodeForPointId: function(pointId) {
        // get the point from the collection
        var point = this.getPointWithId(pointId);

        //get the code
        return this.getAnnotationCodeForPoint(point);
    },
    /**
     * Returns an AnnotationCode object for the secondary annotation of a given point
     * @param pointId
     * @returns {*}
     */
    getSecondaryAnnotationCodeForPointId: function(pointId) {
        // get the point from the collection
        var point = this.getPointWithId(pointId);

        //get the code
        return this.getSecondaryAnnotationCodeForPoint(point);
    },
    /**
     * Returns an AnnotationCode object for the primary annotation of a given point
     * @param point
     * @returns {*}
     */
    getAnnotationCodeForPoint: function(point) {
        //get the code
        return annotationCodeList.find(function(listmodel) {
            return listmodel.get('caab_code')===point.get('annotation_caab_code');
        });
    },
    /**
     * Returns an AnnotationCode object for the secondary annotation of a given point
     * @param point
     * @returns {*}
     */
    getSecondaryAnnotationCodeForPoint: function(point) {
        //get the code
        return annotationCodeList.find(function(listmodel) {
            return listmodel.get('caab_code')===point.get('annotation_caab_code_secondary');
        });
    }
};


// helper functions, to be (possibly) removed pending some API/server changes

function getUsefulCaabRoot(caab_code_id){
    // returns either Biota, Substrate, Relief of Bedform
    var rootTypeText = ['Biota', 'Substrate', 'Relief', 'Bedforms'];
    var caabCodeRoots = ['80000000','82001000','82003000','82002000'];
    var return_code;
    
    if (plain_annotation_list.length === 0){
        // annotation list has not be initialised. This is bad
        return null;
    }
    var currentCode = plain_annotation_list[parseInt(caab_code_id,10)-1];

    if (currentCode.caab_code === '82000000'){
        // Physical ... not useful as roots for broad classification
        return '82000000';
    }

    if (currentCode.caab_code === '00000000'){
        //Not Considered ... not useful as roots for broad classification
        return '00000000';
    }

    if (currentCode.caab_code === '00000001'){
        //unscorable ... not useful as roots for broad classification
        return '00000001';
    }

    if (currentCode.caab_code !== caabCodeRoots[0] && currentCode.caab_code !== caabCodeRoots[1] &&
        currentCode.caab_code !== caabCodeRoots[2] && currentCode.caab_code !== caabCodeRoots[3]){

        parent_text = currentCode.parent.split('/');
        parent_id = parent_text[parent_text.length-2];
        return_code  = getUsefulCaabRoot(parent_id);
    } else {
        return currentCode.caab_code;
    }

    return return_code;
}

function loadPage(offset) {
    fetchThumbnails(offset);
    orchestratorView.thumbnailStripView.render();

    var image = thumbnailImages.first();
    selectedImageId = image.get('id');
    GlobalEvent.trigger("thumbnail_selected_by_id", selectedImageId, image.get('web_location'));
    GlobalEvent.trigger("annotation_set_has_changed"); //XXX triggering this event to fetch new image stats and redraw chart for image progress
}

function fetchThumbnails(offset) {
    var off = {};
    if (offset) off = offset;
    thumbnailImages.fetch({
        data: {
            offset: off
        },
        async: false,
        success: function (model, response, options) {
            currentOffset = offset;
            //alert('currentOffset : ' + currentOffset + ' after fetching meta : ' + thumbnailImages.meta.toSource());
        },
        error: function (model, response, options) {
            alert('Error fetching thumbnails : ' + response);
        }
    });
}

function createPagination(meta) {
    //Create pagination
    var options = thumbnailPaginationOptions(meta);
    $('#pagination').bootstrapPaginator(options);
}

function createBookmark() {
    var url = location.protocol + '//' + location.hostname + (location.port ? ':' + location.port : '') 
              + "/projects/" + projectId + "/annotate/?bid=";
    window.prompt("Permanent URL to this project image.", url + selectedImageId);
}

//-------------------
// NEW SECTION
//-------------------

var ImageCanvasView = Backbone.View.extend({
    model: new PointAnnotation(),
    el: $('div'),
    events: {
        "thumbnail_selected": "thumbnailSelected"
    },
    initialize: function () {

        //bind to the global event, so we can get events from other views
        GlobalEvent.on("thumbnail_selected", this.thumbnailSelected, this);
        GlobalEvent.on("thumbnail_selected_by_id", this.thumbnailSelectedWithId, this);
        GlobalEvent.on("screen_changed", this.screenChanged, this);

        this.resetLeaflet();
    },
    resetLeaflet: function() {
        //destroy everything
        if(this.map != null)
            this.map.remove();

        // create the map for leaflet
        this.map = L.map('ImageViewer', {
            maxZoom: 24,
            //minZoom: 2,
            crs: L.CRS.Simple
        }).setView([150, 200], 14);

        // set the default 3:4 aspect ratio for image bounds
        this.imageBounds = [[0, 0], [300, 400]];

        // init modified ViewCenter plugin
        this.viewCenter = new L.Control.ViewCenter({
            position: 'topleft',
            title: 'Fit to image bounds.',
            forceSeparateButton: true,
            vcLatLng: this.imageBounds,
            vcZoom: 6
	    });

        // add the control
        this.map.addControl(this.viewCenter);

    },
    resetLassoCanvas: function() {
        console.log("resetLassoCanvas");
    },
    findLassoPoints: function() {
        console.log('findLassoPoints')
    },
    initializeLasso: function () {
        console.log('initializeLasso');
    },
    renderSelectedImageById: function (id) {

        // get the url of the image to display
        var imageUrl = $('#' + id).data("web_location");

        // reset leaflet and add the image to the overlay
        this.resetLeaflet();
        var imageOverlay = L.imageOverlay(imageUrl, this.imageBounds);

        /*
        $.ajax({
          type: "HEAD",
          url : imageUrl,
          success: function(message,text,response){},
          error:function(message,text,response){
            $.notify({
                title: 'Oops. The image failed to load, pleaase try again later.',
                text: response.status
            },{
                type: 'danger', // success | info | error
                hide: true,
                icon: false,
                history: false,
                sticker: false
            });
          }
        });
        */

        imageOverlay.addTo(this.map);
        this.map.fitBounds(this.imageBounds, {padding: [0, 0]});

        // bring box to front
        var centerBox = L.polygon([
            [0, 0.45*400],
            [0, 0.55*400],
            [300, 0.55*400],
            [300, 0.45*400]
        ], {
            color: 'yellow',
            fillOpacity: 0.0
        });
        centerBox.addTo(this.map);

        // put the points on the image
        //this.renderPointsForImage();
        GlobalEvent.trigger("image_has_loaded", this);

        return this;
    },
    renderSelectedImage: function (selected) {
        console.log("renderSelectedImage");
    },
    thumbnailSelectedWithId: function (ImageId) {
        //TODO: check
        //this.pointMouseOut();
        this.renderSelectedImageById(ImageId);
    },
    thumbnailSelected: function (selectedPosition) {
        //TODO: check if required?
    },
    screenChanged: function () {
        // no use for this at the moment
    }
});

var ImageToolbarView = Backbone.View.extend({
    el: $('div'),
    events: {},
    initialize: function () {
        var parent = this;

        //bind to the global event, so we can get events from other views
        //GlobalEvent.on("thumbnail_selected", this.thumbnailSelected, this);
        $("#PreviousImageButton").click(function(event) {parent.previousImage(event);});
        $("#NextImageButton").click(function(event) {parent.nextImage(event);});

        $(document).bind('keydown', 'right', function(event) {parent.nextImage(event)});
        $(document).bind('keydown', 'left', function(event) {parent.previousImage(event)});
    },
    previousImage: function(event) {

        // get the index and id of the previous image
        var currentImage = thumbnailImages.findWhere({id: parseInt(selectedImageId)});
        var previousIndex = thumbnailImages.indexOf(currentImage) - 1;

        // if there is previous image send a selection event for it
        if(previousIndex >= 0) {
            var previousImage = thumbnailImages.at(previousIndex);
            var previousId = previousImage.get("id");
            var webLocation = previousImage.get("web_location");

            GlobalEvent.trigger("thumbnail_selected_by_id", previousId, webLocation);
        }
        else { // if there is no image, go back a page
            GlobalEvent.trigger("thumbnail_page_back");
        }

    },
    nextImage: function(event) {

        // get the index and id of the next image
        var currentImage = thumbnailImages.findWhere({id: parseInt(selectedImageId)});
        var nextImageIndex = thumbnailImages.indexOf(currentImage) + 1;

        // if there is next image send a selection event for it
        if(nextImageIndex < thumbnailImages.size()) {

            var nextImage = thumbnailImages.at(nextImageIndex);
            var nextId = nextImage.get("id");
            var webLocation = nextImage.get("web_location");

            this.walkfForwardLabelling(annotationSets.at(0).get("id"), selectedImageId, nextId);

            GlobalEvent.trigger("thumbnail_selected_by_id", nextId, webLocation);
        }
        else { // if there is no image, go forward a page

            //this.walkfForwardLabelling(annotationSets.at(0).get("id"), selectedImageId);

            GlobalEvent.trigger("thumbnail_page_forward");
        }
    },
    walkfForwardLabelling: function(annotationSetId, sourceImageId, destinationImageId) {
        // make url
        var url = "/api/dev/whole_image_annotation/" + annotationSetId + "/walk_forward_labelling/?source_image=" + sourceImageId + "&destination_image=" + destinationImageId;

        // check if walk forward labelling is checked
        if($('#WalkForwardLabelling').is(':checked'))
            $.ajax({
                url: url,
                dataType: "json",
                async: false,
                success: function (response, textStatus, jqXHR) {},
                error: function (model, response, options) {
                    $.notify({
                        title: 'Failed to copy annotations to next image.',
                        text: response.status,
                        type: 'error', // success | info | error
                        hide: true,
                        icon: false,
                        history: false,
                        sticker: false
                    });
                }
            });
    }
});

var PointAnnotationView = Backbone.View.extend({
    imageCanvasView: null,
    initialize: function() {

        //set the map
        this.imageCanvasView = this.options.imageCanvasView;

        GlobalEvent.on("point_clicked", this.pointClicked, this);
        GlobalEvent.on("point_shift_clicked", this.pointShiftClicked, this);
        GlobalEvent.on("point_mouseover", this.pointMouseOver, this);
        GlobalEvent.on("point_mouseout", this.pointMouseOut, this);
        GlobalEvent.on("refresh_point_labels_for_image", this.refreshPointLabelsForImage, this);
        GlobalEvent.on("hide_points", this.hidePoints, this);
        GlobalEvent.on("show_points", this.showPoints, this);
        GlobalEvent.on("deselect_points", this.deselectPoints, this);
        GlobalEvent.on("annotation_to_be_set", this.saveAnnotation, this);
        GlobalEvent.on("qualifier_to_be_set", this.saveQualifier, this);
        GlobalEvent.on("image_points_updated", this.refreshPoints, this);
        GlobalEvent.on("image_has_loaded", this.renderPointsForImage, this);

        // initialise leaflet point markers
        // create gloabl markers for representing state
        // create the icons for the 3 different states - annotated, not annotated, selected
        this.annotatedIcon = L.AwesomeMarkers.icon({
            prefix: 'fa',
            icon: 'check',
            markerColor: 'blue',
            iconColor: 'white'
        });

        this.selectedIcon = L.AwesomeMarkers.icon({
            prefix: 'fa',
            icon: 'circle-o-notch',
            markerColor: 'orange',
            iconColor: 'white',
            spin: 'true'
        });

        this.notAnnotatedIcon = L.AwesomeMarkers.icon({
            prefix: 'fa',
            icon: 'circle-o-notch',
            markerColor: 'red',
            iconColor: 'white'
        });
    },
    render: function() {

    },
    pointClicked: function (thePoint) {
        this.selectPoint(thePoint);

        //refresh the point labels
        this.refreshPointLabelsForImage();
    },
    pointShiftClicked: function (thePoint) {
        //TODO: intelligent point selection
        /*
        // get intelligent points configuration from the cookie, disabled by default
        var intelligentPointsKey = "catamiproject_" + project.get("id");
        var intelligentPoints = ($.cookie(intelligentPointsKey) == "true") ? true : false;

        // if intelligent points is on then do the work
        if (intelligentPoints)
            this.selectSimilarPoints($(thePoint).attr('id'));

        // if it's not on, then tell the user
        else
            $('#similar-points-modal').modal('show');

        //refresh the point labels
        this.refreshPointLabelsForImage();*/
    },
    selectPoint: function (thePoint) {
        //TODO: need this any more?
    },
    selectSimilarPoints: function (selectedPointId) {

        var parent = this;

        var preTime = new Date().getTime();

        //get point colour
        var selectedPoint = PointUtil.getPointWithId(selectedPointId);
        var selectedPointX = selectedPoint.get("x");
        var selectedPointY = selectedPoint.get("y");
        var selectedPointColour = imageSegmentation.getPointColour(selectedPointX, selectedPointY);

        var samePoints = [];
        for (var i = 0; i < points.length; i++) {

            var x = points.at(i).get("x");
            var y = points.at(i).get("y");

            var pointColour = imageSegmentation.getPointColour(x, y);

            if (pointColour[0] == selectedPointColour[0] &&
                pointColour[1] == selectedPointColour[1] &&
                pointColour[2] == selectedPointColour[2] &&
                pointColour[3] == selectedPointColour[3]) {

                samePoints.push(points.at(i));
            }

        }

        for (var i = 0; i < samePoints.length; i++) {
            var point = samePoints[i];
            parent.selectPoint("#" + point.get("id"));
        }

    },
    pointMouseOver: function (thePoint) {
        //TODO: need this any more?
    },
    pointMouseOut: function () {
        //TODO: need this any more?
    },
    hidePoints: function () {
        //TODO: re-enable hide points
    },
    showPoints: function () {
        //TODO: re-enable show points
    },
    /**
     * Refreshes the mouse over labels for points on an image.
     */
    refreshPointLabelsForImage: function () {
        //TODO: need this any more?
    },
    renderPointsForImage: function () {

        var parent = this;

        //destroy all the tooltips before loading new points
        this.pointMouseOut();

        //get the selected image
        var annotationSet = annotationSets.at(0);

        //var image = annotationSet.get("images")[selected];

        //this.disableAnnotationSelector();

        //query the API for the points for the current image
        points.fetch({
            data: { limit: 100, image: selectedImageId, annotation_set: annotationSet.get('id') },
            success: function (model, response, options) {

                //loop through the points and apply them to the image
                points.each(function (point) {

                    // get properties of the point of interest
                    var pointId = point.get('id');

                    var label = point.get('annotation_caab_code');

                    var annotationCode = annotationCodeList.find(function (model) {
                        return model.get('caab_code') === point.get('annotation_caab_code');
                    });

                    var annotationCodeSecondary = '';

                    if (point.get('annotation_caab_code_secondary') !== '') {
                        annotationCodeSecondary = annotationCodeList.find(function (model) {
                            return model.get('caab_code') === point.get('annotation_caab_code_secondary');
                        });
                    }

                    var Y = point.get('y') * 300.0;
                    var X = point.get('x') * 400.0;

                    // create the marker
                    var marker = new L.marker([Y, X]);

                    // decide how to display this point, whether annotated or not
                    //var labelClass = (label === "") ? 'pointNotAnnotated' : 'pointAnnotated';
                    if (label == "")
                        marker.setIcon(parent.annotatedIcon);
                    else
                        marker.setIcon(parent.notAnnotatedIcon);

                    // append the id to the title tag
                    marker.options.title = pointId;

                    // add it to the map
                    marker.addTo(parent.imageCanvasView.map);

                    // define the click handling functions for the markers
                    marker.on('click', function(event) {
                        var clickedMarker = event.target;
                        var iconColour = clickedMarker.options.icon.options.markerColor;

                        // get the annotation on this marker
                        var point = PointUtil.getPointWithId(marker.options.title);
                        var annotationCode = PointUtil.getAnnotationCodeForPoint(point);

                        // workout what state the icon should be changed to
                        var notAnnotated = iconColour == 'orange' && (annotationCode == "" || annotationCode == null);
                        var annotated = iconColour == 'orange' && annotationCode != "" && annotationCode != null;

                        var icon = notAnnotated ? parent.notAnnotatedIcon :
                                   annotated ? parent.annotatedIcon :
                                   parent.selectedIcon;

                        clickedMarker.setIcon(icon);
                    });

                    marker.on('mouseover', function(event) {
                        var point = PointUtil.getPointWithId(marker.options.title);
                        var annotationCode = PointUtil.getAnnotationCodeForPoint(point);
                        var secondaryAnnotationCode = PointUtil.getSecondaryAnnotationCodeForPoint(point);
                        var qualifierText = point.get("qualifier_short_name");
                        var secondaryQualifierText = point.get("qualifier_short_name_secondary");

                        if(annotationCode != null) {
                            var label = "<b>Primary: </b>" + annotationCode.get("code_name")

                            if(qualifierText != "")
                                label += " | " + qualifierText;

                            if(secondaryAnnotationCode != null)
                                label += " </br> <b>Secondary: </b>" + secondaryAnnotationCode.get("code_name");

                            if(secondaryQualifierText != "")
                                label += " | " + secondaryQualifierText;

                            event.target.bindPopup(label);
                            event.target.openPopup();
                        }
                    });

                    marker.on('mouseout', function(event) {
                        event.target.closePopup();
                        event.target.unbindPopup();
                    });

                });

                //update pils
                GlobalEvent.trigger("image_points_updated", this);
            },
            error: function (model, response, options) {
                $.notify({
                    title: 'Failed to load the points for this image. Try refreshing the page.',
                    text: response.status,
                    type: 'error', // success | info | error
                    hide: true,
                    icon: false,
                    history: false,
                    sticker: false
                });
            }
        });

        $("[rel=tooltip]").tooltip();

    },
    refreshPoints: function() {
        var parent = this;

        // refresh the display of points on the map, this should happen after an annotation
        parent.imageCanvasView.map.eachLayer(function (layer) {
            // only get the icon layers
            if(layer.options.icon) {
                // get point based on the id that is appended to the title field
                var point = points.findWhere({id:layer.options.title});

                // update the icon based on the point properties
                var label = point.get('annotation_caab_code');

                (label == '') ? layer.setIcon(parent.notAnnotatedIcon) : layer.setIcon(parent.annotatedIcon);
            }
        });
    },
    saveAnnotation: function(caab_code, annotationType) {
        var parent = this;
        var selectedIds = [];

        //get the selected points
        parent.imageCanvasView.map.eachLayer(function (layer) {
            // only get the icons that are selected
            if(layer.options.icon == parent.selectedIcon) {
                selectedIds.push(layer.options.title);
            }
        });

        //only need a callback function if points greater than 0
        var afterAllSavedCallback;
        if(selectedIds.length > 0)
            afterAllSavedCallback = _.after(selectedIds.length, function() {
                //send out an event for all the other listeners
                GlobalEvent.trigger("annotation_set_has_changed");
                GlobalEvent.trigger("image_points_updated", this);
                GlobalEvent.trigger("refresh_point_labels_for_image", this);
            });

        //save the annotations
        $.each(selectedIds, function(index, id) {

            //need to specify the properties to patch
            var properties  = {};

            // depending on the annotation type, we set different properties
            if(annotationType == "primaryAnnotation")
                properties = { 'annotation_caab_code': caab_code };
            else if(annotationType == "secondaryAnnotation")
                properties = { 'annotation_caab_code_secondary': caab_code };

            var theXHR = points.get(id).save(properties, {
                patch: true,
                headers: {"cache-control": "no-cache"},
                success: function (savedModel, xhr, options) {

                    // do the after save functions
                    afterAllSavedCallback();
                },
                error: function (model, xhr, options) {
                    if (theXHR.status == "201" || theXHR.status == "202") {

                        // do the after save functions
                        afterAllSavedCallback();

                    } else if(theXHR.status == "401") {
                        $.notify({
                            title: 'You don\'t have permission to annotate this image.',
                            text: theXHR.response,
                            type: 'error', // success | info | error
                            hide: true,
                            icon: false,
                            history: false,
                            sticker: false
                        });
                    }
                    else {
                        $.notify({
                            title: 'Failed to save your annotations to the server.',
                            text: theXHR.response,
                            type: 'error', // success | info | error
                            hide: true,
                            icon: false,
                            history: false,
                            sticker: false
                        });
                    }
                }
            });
        });

        GlobalEvent.trigger("annotation_triggered");
    },
    saveQualifier: function(qualifierText, annotationType) {
        var parent = this;
        var selectedIds = [];

        //get the selected points
        parent.imageCanvasView.map.eachLayer(function (layer) {
            // only get the icons that are selected
            if(layer.options.icon == parent.selectedIcon) {
                selectedIds.push(layer.options.title);
            }
        });

        //only need a callback function if points greater than 0
        var afterAllSavedCallback;
        if(selectedIds.length > 0)
            afterAllSavedCallback = _.after(selectedIds.length, function() {
                //send out an event for all the other listeners
                GlobalEvent.trigger("annotation_set_has_changed");
                GlobalEvent.trigger("image_points_updated", this);
                GlobalEvent.trigger("refresh_point_labels_for_image", this);
            });

        //save the annotations
        $.each(selectedIds, function(index, id) {

            //need to specify the properties to patch
            var properties  = {};

            // depending on the annotation type, we set different properties
            if(annotationType == "primaryQualifier")
                properties = { 'qualifier_short_name': qualifierText };
            else if(annotationType == "secondaryQualifier")
                properties = { 'qualifier_short_name_secondary': qualifierText };

            var theXHR = points.get(id).save(properties, {
                patch: true,
                headers: {"cache-control": "no-cache"},
                success: function (savedModel, xhr, options) {

                    // do the after save functions
                    afterAllSavedCallback();
                },
                error: function (model, xhr, options) {
                    if (theXHR.status == "201" || theXHR.status == "202") {

                        // do the after save functions
                        afterAllSavedCallback();

                    } else if(theXHR.status == "401") {
                        $.notify({
                            title: 'You don\'t have permission to annotate this image.',
                            text: theXHR.response,
                            type: 'error', // success | info | error
                            hide: true,
                            icon: false,
                            history: false,
                            sticker: false
                        });
                    }
                    else {
                        $.notify({
                            title: 'Failed to save your annotations to the server.',
                            text: theXHR.response,
                            type: 'error', // success | info | error
                            hide: true,
                            icon: false,
                            history: false,
                            sticker: false
                        });
                    }
                }
            });
        });

        GlobalEvent.trigger("annotation_triggered");
    },
    deselectPoints: function () {
        //TODO: Still needed?
    }
});

var BroadScaleAnnotationView = Backbone.View.extend({
    controls: [],
    imageCanvasView: null,
    initialize: function() {

        //events
        GlobalEvent.on("image_has_loaded", this.loadAnnotations, this);
        GlobalEvent.on("broad_scale_annotation_to_be_set", this.saveBroadScaleAnnotation, this);
        GlobalEvent.on("qualifier_to_be_set", this.saveBroadScaleQualifier, this);
        GlobalEvent.on("fov_percentage_to_be_set", this.saveBroadScaleFOVPercentage, this);
        GlobalEvent.on("annotation_set_has_changed", this.updateControls, this);
        GlobalEvent.on("delete_broad_scale_annotation", this.updateControls, this);
        GlobalEvent.on("broad_scale_annotation_deleted", this.handleAddedDeleted, this);
        GlobalEvent.on("broad_scale_annotation_added", this.handleAddedDeleted, this);
        GlobalEvent.on("add_broad_scale_annotation", this.addBroadScaleLabelWithAnnotation, this);

        //set the canvas view
        this.imageCanvasView = this.options.imageCanvasView;

    },
    render: function() {},
    handleAddedDeleted: function() {
        this.resetControls();
        this.loadAnnotations();
        this.renderAnnotationsForImage();
        this.updateControls();

        //let all the other things get updated
        GlobalEvent.trigger("annotation_set_has_changed");
    },
    loadAnnotations: function() {
        var parent = this;

        //get the selected image
        var annotationSet = annotationSets.at(0);

        // load the annotations
        broadScalePoints.fetch({
            data: { limit: 100, image: selectedImageId, annotation_set: annotationSet.get('id') },
            success: function (model, response, options) {
                parent.renderAnnotationsForImage();
            },
            error: function (model, xhr, options) {
                parent.errorMessage('Failed to load annotations for this image. Try refreshing the page.', xhr.response);
            }
        });
    },
    updateControls: function() {
        for (index in this.controls) {
            this.controls[index].refresh();
        }
    },
    resetControls: function() {
        for (index in this.controls) {
            try {
                this.imageCanvasView.map.removeControl(this.controls[index]);
            } catch(exception) {// dont need to worry if the control is not there
            }
        }
        this.controls = [];
    },
    createAddButton: function() {
        var parent = this;

        var addButton = L.control();

        addButton.onAdd = function (map) {
            this._div = L.DomUtil.create('div'); // create a div with a class "info"

            //this._div.innerHTML = '<button id="AddBroadScaleAnnotation" type="button" class="btn btn-default">Add BSA</button>';

            return this._div;
        };

        addButton.refresh = function() {};
        addButton.addTo(this.imageCanvasView.map);
        this.controls.push(addButton);

        // add the click handler
        $("[id*='AddBroadScaleAnnotation']").click(function(event) {parent.addBroadScaleLabel(event);});
    },
    renderAnnotationsForImage: function() {

        var parent = this;

        //reset the controls
        this.resetControls();

        // create the add new annotation button
        this.createAddButton();

        // render the annotations
        broadScalePoints.each(function (whole_image_point) {
            // create the control
            var info = L.control();

            // get the data for the annotation
            info.iconUrl = whole_image_point.get('owner_icon');
            info.owner = whole_image_point.get('owner');
            info.pointId = whole_image_point.get('id');
            info.annotationCode = whole_image_point.get('annotation_caab_code');
            info.fov_percentage = whole_image_point.get('coverage_percentage');
            info.qualifier = whole_image_point.get('qualifier_short_name');

            console.log(info.owner + " - " + info.iconUrl);

            if (info.fov_percentage < 0){ info.fov_percentage='--'; }

            if (info.annotationCode == ""){
                //info.annotationCode = annotationCodeList.findWhere({caab_code: '00000000'});
                info.label = "Not Set"
                info.style = "redLabel";
            } else {
                info.annotationCode = annotationCodeList.findWhere({caab_code: whole_image_point.get('annotation_caab_code')});
                info.label = info.annotationCode.get('code_name');
                info.style = "blueLabel";

                // give a distinctive style for automated annotations
                //if(whole_image_point.get('owner') == "BenthoBot") {
                //    info.style = "benthobotLabel";
                //}
            }

            // render the annotation
            info.onAdd = function (map) {
                this._div = L.DomUtil.create('div', this.style); // create a div with a class "info"
                this._div.id = this.pointId;

                this.update();

                L.DomEvent.on(this._div, 'click', function(event) {
                    parent.broadScaleLabelSelected(event);
                }, this);

                L.DomEvent.on(this._div, 'mouseover', function() {}, this);

                return this._div;
            };

            // method that we will use to update the control based on feature properties passed
            info.update = function () {
                var annotation = broadScalePoints.findWhere({id: this.pointId});
                var annotationCode = annotationCodeList.findWhere({caab_code: annotation.get('annotation_caab_code')});

                var qualifier = annotation.get('qualifier_short_name');
                var fov_percentage = annotation.get('coverage_percentage');
                var label = "Not set";

                if (annotationCode != null) {
                    label = annotationCode.get('code_name');
                }

                if(qualifier == "")
                    qualifier = "--"

                if(fov_percentage == -1)
                    fov_percentage = "--"

                var icon;
                if (this.owner == "BenthoBot")
                    icon = '<i class="fa fa-cogs" title="BenthoBot"></i>';
                else
                    icon = '<i class="fa fa-user" title="'+ this.owner +'"></i>';

                //this._div.innerHTML = '<h4> ' + this.label + ' </h4><b>' + this.qualifier + ' </b><br />' + this.fov_percentage;
                //this._div.innerHTML = label + " | " + qualifier + " | " + fov_percentage + "% " + "<a id='DeleteBSA-"+ this.pointId + "' href='#' rel='tooltip' data-toggle='tooltip' data-placement='left' title='Delete Annotation'>X</a>";
                this._div.innerHTML = icon + " " + label + " " + "<a id='DeleteBSA-"+ this.pointId + "' href='#' rel='tooltip' data-toggle='tooltip' data-placement='left' title='Delete Annotation'>X</a>";

            };

            info.refresh = function() {
                this.update();
                $(this._div).show();
            }

            info.addTo(parent.imageCanvasView.map);
            parent.controls.push(info);
        });

        //delete handler -- timeout just to let the dom render the labels
        setTimeout(function () {
            $("[id*='DeleteBSA']").click(function(event) {parent.deleteBroadScaleLabel(event);});
        }, 200);

    },
    addBroadScaleLabel: function() {
        var annotationSet = annotationSets.at(0);
        var broad_scale_annotation = new WholeImageAnnotation({ 'annotation_caab_code': '',
                                                                'image':'/api/dev/image/'+selectedImageId+'/',
                                                                'annotation_set':'/api/dev/annotation_set/'+annotationSet.get('id')+'/'});

        broadScalePoints.create(broad_scale_annotation,{
            success:function() {
                GlobalEvent.trigger("broad_scale_annotation_added");
            }
        });
    },
    addBroadScaleLabelWithAnnotation: function(codeToSet) {
        var annotationSet = annotationSets.at(0);
        var broad_scale_annotation = new WholeImageAnnotation({ 'annotation_caab_code': codeToSet,
                                                                'image':'/api/dev/image/'+selectedImageId+'/',
                                                                'annotation_set':'/api/dev/annotation_set/'+annotationSet.get('id')+'/'});

        broadScalePoints.create(broad_scale_annotation,{
            success:function() {
                GlobalEvent.trigger("broad_scale_annotation_added");
            }
        });
    },
    deleteBroadScaleLabel: function(event) {
        var parent = this;

        var deleteId = $(event.target).attr('id').replace("DeleteBSA-", "");
        console.log(deleteId);
        var objectsToRemove = broadScalePoints.get(parseInt(deleteId));

        if (objectsToRemove != null)
            objectsToRemove.destroy({
                success: function(model, response, options) {
                    GlobalEvent.trigger("broad_scale_annotation_deleted");
                },
                error: function (model, xhr, options) {
                    parent.errorMessage("Failed to delete annotation.", xhr.response);
                }
            });
    },
    broadScaleLabelSelected: function(event) {

        var target = $(event.target);

        // if we clicked the remove button, then don't continue
        if(target.attr("id").indexOf("DeleteBSA") != -1)
            return;

        // get the colour of the select label
        var cssClass = target.attr("class");

        // if it's undefined maybe text was selected inside thc control, get the parent class
        if (cssClass == null) {
            cssClass = target.parent().attr("class");
            target = target.parent();
        }

        // if blue or red set to orange
        if (target.hasClass("redLabel") || target.hasClass("blueLabel")) {
            //reset the label colours - so that any orange is deselected
            this.resetLabelColours();

            target.removeClass("redLabel").removeClass("blueLabel").addClass("orangeLabel");
        }
        else if (target.hasClass("orangeLabel")) { // if orange, reset
            this.resetLabelColours();
        }
    },
    resetLabelColours: function() {
        // clear all of the controls
        $(".redLabel, .orangeLabel, .blueLabel").each(function() {
            // get the id
            var annotationId = $(this).attr('id');
            //alert(annotationId);

            // get the annotation
            var annotationCode = broadScalePoints.findWhere({id: parseInt(annotationId)}).get('annotation_caab_code');

            // if no code make red
            if (annotationCode == "") {
                $(this).removeClass("blueLabel").removeClass("orangeLabel").addClass("redLabel");
            }
            else { // if has a code make blue
                $(this).removeClass("redLabel").removeClass("orangeLabel").addClass("blueLabel");
            }

        });
    },
    getSelectedBroadScaleAnnotationId: function() {
        // the selected item will be the div with orange label css class set
        return $(".orangeLabel").attr('id');
    },
    saveBroadScaleAnnotation: function(annotationCode, annotationType) {
        // find the selected annotation
        var annotationId = this.getSelectedBroadScaleAnnotationId();

        if (annotationId != null) {
            // set the properties and save
            var properties = { 'annotation_caab_code': annotationCode };
            this.saveAnnotation(annotationId, properties);
        }
    },
    saveBroadScaleQualifier: function(qualifierText, annotationType) {
        // find the selected annotation
        var annotationId = this.getSelectedBroadScaleAnnotationId();

        if (annotationId != null) {
            // set the properties and save
            var properties = { 'qualifier_short_name': qualifierText};
            this.saveAnnotation(annotationId, properties);
        }
    },
    saveBroadScaleFOVPercentage: function(fovPercentageText, annotationType) {
        //find the selected annotation
        var annotationId = this.getSelectedBroadScaleAnnotationId();

        if (annotationId != null) {
            // set the properties and save
            var properties = { 'coverage_percentage': fovPercentageText};
            this.saveAnnotation(annotationId, properties);
        }
    },
    saveAnnotation: function(annotationId, properties) {
        var parent = this;
        var theXHR  = broadScalePoints.get(annotationId).save(properties, {
            patch: true,
            headers: {"cache-control": "no-cache"},
            success: function (model, xhr, options) {
                GlobalEvent.trigger("annotation_set_has_changed");
            },
            error: function (model, xhr, options) {
                parent.errorMessage("Failed saving annotation, please try refreshing the page.", theXHR.response);
                GlobalEvent.trigger("annotation_set_has_changed");
            }
        });
    },
    errorMessage: function(errorTitle, errorText) {
        $.notify({
            title: errorTitle,
            text: errorText,
            type: 'error', // success | info | error
            hide: true,
            icon: false,
            history: false,
            sticker: false
        });
    }
});

var AnnotationSelectionView = Backbone.View.extend({

    el: "#AnnotationSelectionTab",
    events: {
        'click #ActionButtonPanel': 'controlButtonClicked',

        'click #BroadScaleAnnotationButton': 'showAnnotationPanel',
        'click #BroadScaleQualifierButton': 'showQualifierPanel',
        'click #FOVPercentageButton': 'showFOVPercentagePanel',

        'click #PrimaryAnnotationButton': 'showAnnotationPanel',
        'click #SecondaryAnnotationButton': 'showAnnotationPanel',
        'click #PrimaryQualifierButton': 'showQualifierPanel',
        'click #SecondaryQualifierButton': 'showQualifierPanel',

        'click #QualifiersPanel a': 'qualifierClicked',
        'click #FOVPercentagePanel a': 'fovPercentageClicked',

        'change select': 'categorySelected'
    },
    initialize: function(options) {},
    render: function() {

        if(this.options.broadScaleProject) { // BS project
            //show broad scale buttons and hide fine scale
            $("#BroadScaleButtons").show();
            $("#FineScaleButtons").hide();

            //click the BSA button
            $("#BroadScaleAnnotationButton").click();

        } else { // FS project
            $("#BroadScaleButtons").hide();
            $("#FineScaleButtons").show();

            //click the FSA button
            $("#PrimaryAnnotationButton").click();
        }

        this.renderCategorySelect();
        this.renderAnnotationPanel();
        this.renderQualifierPanel();
        this.renderFOVPercentagePanel();
    },
    renderCategorySelect: function() {

        // chose the scheme version
        var mangroveScheme = annotationSchemes.findWhere({"name": "Mangrove Watch Classification", "version": "1.0"});

        // filter based on version
        var mangroveCodeList = annotationCodeList.where({"annotation_scheme": mangroveScheme.url()});

        // convert the array of models to a backbone collection - so we can use the pluck method
        mangroveCodeList = annotationCodeList.reset(mangroveCodeList);

        var categories = mangroveCodeList.pluck('category_name');
        categories = _.uniq(categories);

        for(var i=0; i<categories.length; i++) {
            var categoryReadable = categories[i].replace(/:/g, " > ");
            $('#CategorySelector').append($('<option>', {value:categories[i], text:categoryReadable}));
        }

        // render the select box
        $(".chosen-select").chosen();
    },
    renderAnnotationPanel: function() {
        var parent = this;

        // render the table
        var tableRef = document.getElementById('AnnotationPanel').getElementsByTagName('tbody')[0];

        var mangroveScheme = annotationSchemes.findWhere({"name": "Mangrove Watch Classification", "version": "1.0"});
        var categories = annotationCodeList.pluck('category_name');

        categories = _.uniq(categories);

        for(var j=categories.length-1; j>=0; j--) {

            // get only the codes that conform to the mangrove watch scheme
            var mangroveCodeList = annotationCodeList.where({"category_name": categories[j], "annotation_scheme": mangroveScheme.url()});

            for(var i=mangroveCodeList.length-1; i>=0; i--) {

                var newRow = tableRef.insertRow(0);
                newRow.id = categories[j] + mangroveCodeList[i].get("caab_code");
                newRow.className = "annotationPanelItem";

                // Insert a cell in the row at index 0
                var newCell  = newRow.insertCell(0);

                var a = document.createElement('a');
                a.title = mangroveCodeList[i].get("code_name");
                a.href = "#";

                var caab = mangroveCodeList[i].get("caab_code");
                var text = mangroveCodeList[i].get("code_name");

                var newText  = document.createTextNode(text);
                a.appendChild(newText);

                a.setAttribute("rel", "tooltip");
                a.setAttribute("data-toggle", "tooltip");
                a.setAttribute("data-placement", "left");
                a.setAttribute("title", mangroveCodeList[i].get("code_name"));
                a.setAttribute("id", caab);

                // Append a text node to the cell
                newCell.appendChild(a);
                //newCell.bgColor = "#2987c1";

                // handle the cell clicks
                $(newRow).click(function (e) {

                    var cell = e.target;
                    console.log(e.target);
                    if( $(e.target).is('td') )
                         cell = $(e.target).children("a");


                    var annotationType = "broadScaleAnnotation";

                    // fire off an event
                    if(annotationType == 'broadScaleAnnotation') {
                        GlobalEvent.trigger("add_broad_scale_annotation", $(cell).attr("id"));
                        //GlobalEvent.trigger("broad_scale_annotation_to_be_set", $(cell).attr("id"), annotationType);
                    }
                });
            }

            // only create a header if we have items for it
            if(mangroveCodeList.length > 0) {
                var newHeaderRow = tableRef.insertRow(0);
                newHeaderRow.id = categories[j];
                newHeaderRow.className = "annotationPanelHeader";

                // Insert a cell in the row at index 0
                var newHeaderCell = newHeaderRow.insertCell(0);


                var caab = "";
                var text = categories[j].replace(/:/g, " > ");

                var newHeaderText = document.createTextNode(text);
                newHeaderCell.appendChild(newHeaderText);
                //newHeaderCell.bgColor = "#696969";
            }
        }

        return this;
    },
    renderQualifierPanel: function() {
        // table already in html, but we want to hide to start with
        $("#QualifiersPanel").hide();
    },
    renderFOVPercentagePanel: function() {
        // table already in html, but we want to hide to start with
        $("#FOVPercentagePanel").hide();
    },
    showAnnotationPanel: function() {
        $("#FOVPercentagePanel").hide();
        $("#QualifiersPanel").hide();
        $("#AnnotationPanel").show();
    },
    showQualifierPanel: function() {
        $("#FOVPercentagePanel").hide();
        $("#AnnotationPanel").hide();
        $("#QualifiersPanel").show();
    },
    showFOVPercentagePanel: function() {
        $("#AnnotationPanel").hide();
        $("#QualifiersPanel").hide();
        $("#FOVPercentagePanel").show();
    },
    qualifierClicked: function(event) {
        var qualifierText = $(event.target).text();

        // fire off an event
        GlobalEvent.trigger("qualifier_to_be_set", qualifierText, this.getSelectedAnnotationType());
    },
    fovPercentageClicked: function(event) {
        var fovPercentageText = $(event.target).text().replace("%","");

        // fire off an event
        GlobalEvent.trigger("fov_percentage_to_be_set", fovPercentageText, this.getSelectedAnnotationType());
    },
    categorySelected: function(event) {

        // get the selected categories
        var selectedCategories = $(event.target).val() || [];

        // make all table rows invisible in the annotation panel
        $("tr").hide();

        // make visible the rows which have the desired category items
        for(var i=0; i<selectedCategories.length; i++)
            $( "tr[id*='"+ selectedCategories[i] +"']").fadeIn();

        // if none selected then make all visible
        if(selectedCategories.length == 0)
            $("tr").fadeIn();
    },
    getSelectedAnnotationType: function() {
        // get the type of annotation to be set
        var primaryAnnotation = $("#PrimaryAnnotationButton").hasClass("active");
        var primaryQualifier = $("#PrimaryQualifierButton").hasClass("active");
        var secondaryAnnotation = $("#SecondaryAnnotationButton").hasClass("active");
        var secondaryQualifier = $("#SecondaryQualifierButton").hasClass("active");

        var broadScaleAnnotation = $("#BroadScaleAnnotationButton").hasClass("active");
        var broadScaleQualifier = $("#BroadScaleQualifierButton").hasClass("active");
        var broadScaleFOVPercentage = $("#FOVPercentageButton").hasClass("active");

        var annotationType = primaryAnnotation ? 'primaryAnnotation' :
                           primaryQualifier ? 'primaryQualifier' :
                           secondaryAnnotation ? 'secondaryAnnotation' :
                           secondaryQualifier ? 'secondaryQualifier' :
                           broadScaleAnnotation ? 'broadScaleAnnotation' :
                           broadScaleQualifier ? 'broadScaleQualifier' :
                           'broadScaleFOVPercentage';

        return annotationType;
    }
});