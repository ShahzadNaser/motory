frappe.listview_settings["Serial No"] = {
    add_fields: ["car_status_cf"],
    formatters: {
        car_status_cf: function (value, df, doc) {
        var car_status_cf_color = {
          "Available":"green",
          "Booked":"blue",
          "Returned":"orange",
          "Sold Out":"yellow",
          "Damage":"red"          
        };
        let color = car_status_cf_color[value]
        return `<div class="list-row-col hidden-xs ellipsis">
            <span class="indicator-pill ${color} filterable ellipsis" data-filter="status,=,${value}">
          <span class="ellipsis"> ${value}</span>
        <span>
          </span></span>
        </div>`
      }
    },
  };