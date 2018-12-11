// Todo: try to remove most of these global variables

// Variables for a selected geometry
var name;
var description;
var shapeType; // centerpoint, shape or area
var objectName; // Name of the entry at update of an existing entry


var captureCoordinates = false; // Boolean if clicks on map should be captured as coordinates
var marker = false; // Temporary marker for point coordinate
var geoJsonArray = []; // Polygon coordinates storage
var drawnPolygon = L.featureGroup();
var layer;
var newLayer = false;
var editedLayer = false;

/* Controls with EasyButton */
L.Control.EasyButtons = L.Control.extend({
    onAdd: function () {
        var container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
        this.link = L.DomUtil.create('a', 'leaflet-bar-part', container);
        this._addImage()
        this.link.href = '#';
        L.DomEvent.on(this.link, 'click', this._click, this);
        this.link.title = this.options.title;
        return container;
    },
    _click: function (e) {
        L.DomEvent.stopPropagation(e);
        L.DomEvent.preventDefault(e);
        this.intendedFunction();
    },
    _addImage: function () {
        var extraClasses = this.options.intentedIcon.lastIndexOf('fa', 0) === 0 ? ' fa fa-lg' : ' glyphicon';
        L.DomUtil.create('i', this.options.intentedIcon + extraClasses, this.link);
    }
});

polygonButton = new L.Control.EasyButtons({
    position: 'topright',
    intentedIcon: 'fa-pencil-square-o',
    title: translate['map_info_shape']
})
polygonButton.intendedFunction = function() {drawGeometry('shape');}
map.addControl(polygonButton);

areaButton = new L.Control.EasyButtons({
    position: 'topright',
    intentedIcon: 'fa-circle-o-notch',
    title: translate['map_info_area']
})
areaButton.intendedFunction = function() {drawGeometry('area');}
map.addControl(areaButton);

pointButton = new L.Control.EasyButtons({
    position: 'topright',
    intentedIcon: 'fa-map-marker',
    title: translate['map_info_point']
})
pointButton.intendedFunction = function () {drawGeometry('centerpoint');}
map.addControl(pointButton);

inputForm = L.control();
inputForm.onAdd = function (map) {
    div = L.DomUtil.create('div', 'mapFormDiv');
    div.innerHTML = `
        <form id="geometryForm" onmouseover="interactionOff()" onmouseout="interactionOn()">
            <span id="closeButton" title="` + translate["map_info_close"] + `" onclick="closeForm()" class="fa">X</span>
            <span id="inputFormTitle"></span>
            <p id="inputFormInfo"></p>
            <input type="text" id="nameField" placeholder="Enter a name if desired" />
            <textarea rows="3" cols="70" id="descriptionField" placeholder="` + translate["map_info_description"] + `"/></textarea>
            <div id="coordinatesDiv">
                <div style="display:block;clear:both;">
                    <label for='easting'>Easting</label>
                    <input type="text" style="margin-top:0.5em;" oninput="check_coordinates_input()" id="easting" placeholder="decimal degrees" />
                </div>
                <div style="display:block;clear:both;">
                    <label for='northing'>Northing</label>
                    <input type="text" style="margin-top:0.5em;" oninput="check_coordinates_input()" id="northing" placeholder="decimal degrees" />
                </div>
            </div>
            <div style="clear:both;"></div>
            <input type="button" id="saveButton" disabled value="` + translate["save"] + `" onclick="saveForm('` + shapeType + `')" />
        </form>`;
    return div;
};

map.on('click', function(e) {
    if (captureCoordinates && shapeType == 'centerpoint') {
        $('#saveButton').prop('disabled', false);
        if (marker) {  // Marker already exists so move it
            marker.setLatLng(e.latlng);
            marker.on('dragend', function (event) {
                var marker = event.target;
                position = marker.getLatLng();
                $('#northing').val(position.lat);
                $('#easting').val(position.lng);
            });
        } else {  // No marker exists so create it
            var marker = new L.marker(e.latlng, {draggable: true, icon: newIcon});
            marker.addTo(map);
            wgs84 = (marker.getLatLng());
            $('#northing').val(wgs84.lat);
            $('#easting').val(wgs84.lng);
        }
        wgs84 = marker.getLatLng();
        marker.on('dragend', function (event) {
            var marker = event.target;
            position = marker.getLatLng();
            $('#northing').val(position.lat);
            $('#easting').val(position.lng);
        });
        $('#northing').val(wgs84.lat);
        $('#easting').val(wgs84.lng);
    } else if (captureCoordinates) {
        $('#saveButton').prop('disabled', false);
    }
});

map.on('draw:created', function (e) {
    drawnPolygon.addLayer(e.layer);
    layer = e.layer;
    if (shapeType == 'centerpoint') {
        coordinates = layer.getLatLng();
        shapeSyntax = 'ST_GeomFromText(\'POINT(' + (' ' + coordinates.lng + ' ' + coordinates.lat) + ')\',4326);'
    } else {
        geoJsonArray = [];
        coordinates = layer.getLatLngs()[0];
        for (i = 0; i < coordinates.length; i++) {
            geoJsonArray.push('[' + coordinates[i].lng + ',' + coordinates[i].lat + ']');
        }
        geoJsonArray.push('[' + coordinates[0].lng + ',' + coordinates[0].lat + ']'); // Add first xy again as last xy to close polygon
    }
    $('#saveButton').prop('disabled', false);
});

function closeForm(withoutSave = true) {
    inputForm.remove(map);
    $('.leaflet-right .leaflet-bar').show();
    interactionOn();
    $('#map').css('cursor', '');
    if (shapeType != 'centerpoint' && withoutSave) {
        drawnPolygon.removeLayer(layer);
        drawLayer.disable();
    }
    if (marker) {
        map.removeLayer(marker);
    }
    captureCoordinates = false; // Important that this is the last statement
}

function drawGeometry(selectedType) {
    shapeType = selectedType;
    map.addControl(inputForm);
    if (selectedType == 'centerpoint') {
        $('#coordinatesDiv').show();
    } else {
        captureCoordinates = false;
        drawLayer = new L.Draw.Polygon(map);
        map.addLayer(drawnPolygon);
        drawLayer.enable();
        $('#coordinatesDiv').hide();
    }
    $('#inputFormTitle').text(selectedType.substr(0,1).toUpperCase() + selectedType.substr(1));
    $('#inputFormInfo').text(translate['map_info_' + selectedType]);
    $('.leaflet-right .leaflet-bar').hide();
}

function saveForm(shapeType) {

    name = $('#nameField').val().replace(/\"/g,'\\"');
    description = $('#descriptionField').val().replace(/\"/g,'\\"');
    if (typeof newLayer == 'object') {
        saveEditedGeometry(shapeType);
        newLayer.remove(map);
        newLayer = false;
    } else {
        saveNewGeometry(shapeType);
    }
}

function saveEditedGeometry(shapeType) {
    if (feature.properties.shapeType == 'centerpoint') {
        // Remove former point
        points = JSON.parse($('#gis_points').val());
        $.each(points, function (key, value) {
            if (value.properties.id == feature.properties.id) {
                points.splice(key, 1);
                return false;
            }
        });
        // Add new point
        point =
            `{"type": "Feature", "geometry":` +
            `{"type": "Point", "coordinates": [` + $('#easting').val() + `,` + $('#northing').val() + `]},` +
            `"properties":{"name": "` + name + `", "description": "` + description + `", "shapeType": "centerpoint"}}`;
        points.push(JSON.parse(point));
        $('#gis_points').val(JSON.stringify(points));
        editedLayer = L.marker(newLayer.getLatLng(), {icon: editedIcon}).addTo(map);
        editedLayer.bindPopup(buildPopup(JSON.parse(point), 'edited'));
    } else {
        // Remove former polygon
        polygons = JSON.parse($('#gis_polygons').val());
        $.each(polygons, function (key, value) {
            if (value.properties.id == feature.properties.id) {
                polygons.splice(key, 1);
                return false;
            }
        });
        coordinates = '[[' + geoJsonArray.join(',') + ']]'
        polygon =
            `{"type": "Feature", "geometry":` +
            `{"type": "Polygon", "coordinates": ` + coordinates + `},` +
            `"properties":{"name": "` + name + `", "description": "` + description + `", "shapeType": "` + shapeType + `"}}`;
        polygons.push(JSON.parse(polygon));
        $('#gis_polygons').val(JSON.stringify(polygons));
        editedLayer = L.polygon(newLayer.getLatLngs()).addTo(map);
        editedLayer.setStyle({fillColor: '#686868', color: '#686868'});
    }
    closeForm(false);
}

function saveNewGeometry(shapeType) {
    if (shapeType == 'centerpoint') {
        point =
            `{"type": "Feature", "geometry":` +
            `{"type": "Point", "coordinates": [` + $('#easting').val() + `,` + $('#northing').val() + `]},` +
            `"properties":{"name": "` + name + `", "description": "` + description + `", "shapeType": "centerpoint"}}`;
        points = JSON.parse($('#gis_points').val());
        points.push(JSON.parse(point));
        $('#gis_points').val(JSON.stringify(points));
        newMarker = L.marker(([$('#northing').val(), $('#easting').val()]), {icon: editedIcon}).addTo(map);
        newMarker.bindPopup(buildPopup(JSON.parse(point), 'edited'));
        marker = false;  // unset the marker
    } else {
        polygon =
            `{"type": "Feature", "geometry":` +
            `{"type": "Polygon", "coordinates":[[` + geoJsonArray.join(',') + `]]},
            "properties":{"name": "` + name + `", "description": "` + description + `", "shapeType": "` + shapeType + `"}}`;
        polygons = JSON.parse($('#gis_polygons').val());
        polygons.push(JSON.parse(polygon));
        $('#gis_polygons').val(JSON.stringify(polygons));
        layer.bindPopup(buildPopup(JSON.parse(polygon), 'edited'));
        layer.addTo(map);
    }
    closeForm(false);
}

function deleteGeometry() {
    // Remove layer of geometry, remove geometry from form field value
    if (typeof(editLayer) == 'object') {map.removeLayer(editLayer);}
    if (typeof(editMarker) == 'object') {map.removeLayer(editMarker);}
    if (feature.properties.shapeType == 'centerpoint') {
        points = JSON.parse($('#gis_points').val());
        $.each(points, function (key, value) {
            if (value.properties.id == feature.properties.id) {
                points.splice(key, 1);
                return false;
            }
        });
        $('#gis_points').val(JSON.stringify(points));
    } else {
        polygons = JSON.parse($('#gis_polygons').val());
        $.each(polygons, function (key, value) {
            if (value.properties.id == feature.properties.id) {
                polygons.splice(key, 1);
                return false;
            }
        });
        $('#gis_polygons').val(JSON.stringify(polygons)); // write array back to form field
    }
}

function editGeometry() {
    shapeType = feature.properties.shapeType;
    map.closePopup();
    map.addControl(inputForm);
    $('#inputFormTitle').text(shapeType.substr(0,1).toUpperCase() + shapeType.substr(1));
    $('#inputFormInfo').text(translate['map_info_' + shapeType]);
    $('#nameField').val(feature.properties.name);
    $('#descriptionField').val(feature.properties.description);
    $('.leaflet-right .leaflet-bar').hide();
    if (feature.properties.shapeType == 'centerpoint') {
        newLayer = L.marker(editLayer.getLatLng(), {draggable: true, icon: editIcon}).addTo(map);
        wgs84 = newLayer.getLatLng();
        $('#northing').val(wgs84.lat);
        $('#easting').val(wgs84.lng);
        newLayer.bindPopup(feature, 'edit');
        newLayer.on('dragend', function (event) {
            newMarker = event.target;
            position = newMarker.getLatLng();
            $('#northing').val(position.lat);
            $('#easting').val(position.lng);
            $('#saveButton').prop('disabled', false);
        });
        layer.remove(marker);
    } else {
        $('#coordinatesDiv').hide();
        newLayer = L.polygon(editLayer.getLatLngs()).addTo(map);
        // Workaround for Leaflet draw bug: https://github.com/Leaflet/Leaflet.draw/issues/804
        newLayer.options.editing || (newLayer.options.editing = {});
        newLayer.editing.enable();
        newLayer.bindPopup(feature, 'edit');
        newLayer.on('edit', function () {
            $('#saveButton').prop('disabled', false);
            geoJsonArray = [];
            coordinates = newLayer.getLatLngs()[0];
            for (i = 0; i < coordinates.length; i++) {
                geoJsonArray.push('[' + coordinates[i].lng + ',' + coordinates[i].lat + ']');
            }
            // Add first xy again as last xy to close polygon
            geoJsonArray.push('[' + coordinates[0].lng + ',' + coordinates[0].lat + ']');
            layer.remove(feature);
        });
    }
}

function interactionOn() {
    // Enable interaction with map e.g. if cursor leaves form
    captureCoordinates = true;
    map.dragging.enable();
    map.touchZoom.enable();
    map.doubleClickZoom.enable();
    map.scrollWheelZoom.enable();
    map.boxZoom.enable();
    map.keyboard.enable();
    if (map.tap) {
        map.tap.enable();
    }
    $('#map').css( 'cursor', 'crosshair');
}

function interactionOff() {
    // Disable interaction with map e.g. if cursor is over a form
    captureCoordinates = false;
    map.dragging.disable();
    map.touchZoom.disable();
    map.doubleClickZoom.disable();
    map.scrollWheelZoom.disable();
    map.boxZoom.disable();
    map.keyboard.disable();
    if (map.tap) {
        map.tap.disable();
    }
}
