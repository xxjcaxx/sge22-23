/** @odoo-module **/
export {MyComponent};
const { useState } = owl.hooks;
const { xml } = owl.tags;
const FormRenderer = require("web.FormRenderer"); 
const { Component } = owl; 
const { ComponentWrapper } = require("web.OwlCompatibility"); 



class MyComponent extends Component {
    setup() {
        this.state = useState({ value: 1 });
    }

    increment() {
        this.state.value++;
    }
}
MyComponent.template = xml
    `<div t-on-click="increment">
        <t t-esc="state.value">
    </div>`;

FormRenderer.include({
    async _render() { 
        await this._super(...arguments); 

        for(const element of this.el.querySelectorAll(".proves_component")) { 
            (new ComponentWrapper(this, MyComponent)) 
                .mount(element) 
        } 
    } 
})