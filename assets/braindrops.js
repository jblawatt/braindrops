
var app = new Marionette.Application();


var Drop = Backbone.Model.extend({
    urlRoot: "/api/drops",
    defaults: {id: null, message:null, datetime: null, tags: []}
});
var DropColl = Backbone.Collection.extend({
    model: Drop,
    url: "/api/drops"
});

var DropView = Marionette.View.extend({
    template: '#drop-template',
    events: {
        'click .drop-button-delete': function (evt) {
            evt.preventDefault();
            if (confirm("what, sure??")) {
                this.model.destroy({
                    success: function () {
                        app.coll.fetch();
                    }
                });
            }
        }
    },
    attributes: function () {
        return {
            'data-id': this.model.get("id"),
            'style': 'display: none'
        };
    },
    templateContext: function () {

        let tags = _.map(this.model.get("tags"), (tag) => {
            return {
                tag: tag,
                letter: tag.toUpperCase()[0],
                className: "mdl-color--purple"
            }
        });
        return {
            tags: tags
        };
    },
    onRender: function () {
        this.$el.fadeIn();
    }
});


var DropCompView = Marionette.CompositeView.extend({
    template: '#drop-comp-template',
    childView: DropView
});


var DropFormView = Marionette.View.extend({
    template: '#drop-form-template',
    events: {
        'submit form': 'onFormSubmit'
    },
    ui: {
        dropInput: '[name="drop-message"]'
    },
    onFormSubmit: function (event) {
        var message, drop;
        event.preventDefault();
        message = this.ui.dropInput.val();
        if (!message) {
            alert("no message, no drop");
            return;
        }
        drop = new Drop({message: message});
        drop.save(null, {
            success: () => {
                app.coll.add(drop, {at: 0});
            }
        });
        this.ui.dropInput.val(null);
        this.ui.dropInput.focus();
    }
});


document.addEventListener("DOMContentLoaded", function () {
    app.start();
});

app.on("start", function () {

    var coll = app.coll = new DropColl();

    var compView = new DropCompView({
        collection: coll,
        el: document.getElementById("drop-comp-container")
    });

    compView.render();
    coll.fetch();

    var inputView = new DropFormView({
        el: document.getElementById("drop-form-container")
    });

    inputView.render();

});

