
var sourceImage ;
var targetRoot;
var maState;

frappe.ui.form.on("Purchase Receipt", {
  setup:function(frm){

    frm.set_query('letters', 'items', (frm,cdt,cdn) => {
      return {
          filters: {
              "is_numeric":0
          }
      }            
    });
    frm.set_query('numbers', 'items', (frm,cdt,cdn) => {
      return {
          filters: {
              "is_numeric":1
          }
      }            
    });
  },
	// onload_post_render: function(frm) {
  //   $(frm.fields_dict['car_structure_html'].wrapper)
  //   .html('<div  style="position: relative; display: flex;flex-direction: column;align-items: center;justify-content: center;padding-top: 50px;"> \
  //   <img  id="sourceImage"   src="/assets/motory/image/car_structure.png" style="max-width: 900px; max-height: 80%;"  crossorigin="anonymous" /> \
  //   <img  id="sampleImage"   src="/assets/motory/image/car_structure.png"  style="max-width: 900px; max-height: 100%; position: absolute;" crossorigin="anonymous" /> \
  //   </div>');

  //   setSourceImage(document.getElementById("sourceImage"));

  //   const sampleImage = document.getElementById("sampleImage");
  //   sampleImage.addEventListener("click", () => {
  //     showMarkerArea(sampleImage);
  //   });      
  // }
	refresh: function(frm) {
	}
});

frappe.ui.form.on("Purchase Receipt Item", {
  numbers:function(frm,cdt,cdn){
    var item = frappe.get_doc(cdt, cdn);
    frappe.model.set_value(cdt, cdn, "car_plate_no_cf", (item.letters || '') + '-' + (item.numbers || ''));
  },
  letters:function(frm,cdt,cdn){
    var item = frappe.get_doc(cdt, cdn);
    frappe.model.set_value(cdt, cdn, "car_plate_no_cf", (item.letters || '') + '-' + (item.numbers || ''));
  }
});
function setSourceImage(source) {
  sourceImage = source;
  targetRoot = source.parentElement;
}

function showMarkerArea(target) {
  const markerArea = new markerjs2.MarkerArea(sourceImage);
    markerArea.renderImageQuality = 0.5;
    markerArea.renderImageType = 'image/jpeg';

  // since the container div is set to position: relative it is now our positioning root
  // end we have to let marker.js know that
  markerArea.targetRoot = targetRoot;
  markerArea.addRenderEventListener((imgURL, state) => {
    target.src = imgURL;
    // save the state of MarkerArea
    cur_frm.doc.car_structure_annotation=JSON.stringify(state)
   
    cur_frm.set_value('annotated_car_image_cf', imgURL)
    cur_frm.save()
  });
  markerArea.show();
  // if previous state is present - restore it
  if (cur_frm.doc.car_structure_annotation) {
    markerArea.restoreState(JSON.parse(cur_frm.doc.car_structure_annotation));
  }
}


