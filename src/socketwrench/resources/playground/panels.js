class LeftPanel extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    box-sizing: border-box;
                    position: absolute;
                    width: 100vw;
                    height: 100%;
                    z-index: 1;
                    padding: 20px;
                    overflow-y: auto;
                    overflow-x: hidden;
                }
            </style>
            <slot></slot>
        `;
    }
}

class RightPanel extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    box-sizing: border-box;
                    position: absolute;
                    left: 36vw;
                    width: 64vw;
                    max-width: 64vw;
                    height: 100%;
                    max-height: 100%;
                    z-index: 2;
                    padding: 20px;
                    overflow: auto;
                }
            </style>
            <slot></slot>
        `;
    }
}

class PanelDivider extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    position: absolute;
                    box-sizing: border-box;
                    left: 36vw;
                    width: 5px;
                    height: 100%;
                    background-color: gray;
                    cursor: ew-resize;
                    z-index: 3;
                }
            </style>
            <slot></slot>
        `;
        this.dragging = false;
        this.onMousedown = this.onMousedown.bind(this);
        this.onMouseMove = this.onMouseMove.bind(this);
        this.onMouseUp = this.onMouseUp.bind(this);
        this.addEventListener('mousedown', this.onMousedown);


    }

    onMousedown(e) {
        this.dragging = true;
        document.addEventListener('mousemove', this.onMouseMove);
        document.addEventListener('mouseup', this.onMouseUp);
    }
    onMouseMove(e) {
        if (!this.dragging) return;
        let dividerPos = e.clientX;
        this.style.left = dividerPos + 'px';
        this.nextElementSibling.style.left = dividerPos + 'px';
        this.nextElementSibling.style.width = (window.innerWidth - dividerPos) + 'px';
        this.nextElementSibling.style.maxWidth = (window.innerWidth - dividerPos) + 'px';
    }

    onMouseUp() {
        this.dragging = false;
        document.removeEventListener('mousemove', this.onMouseMove);
        document.removeEventListener('mouseup', this.onMouseUp);
    }
}

class PanelContainer extends HTMLElement {
    constructor() {
        super();
        this.style.boxSizing = "border-box";
        document.addEventListener('DOMContentLoaded', this.onDOMContentLoaded.bind(this));

    }
    onDOMContentLoaded() {
        // Create a divider element
        const divider = document.createElement('panel-divider');

        let leftPanel = this.querySelector('left-panel');
        let rightPanel = this.querySelector('right-panel');
        console.log(leftPanel, rightPanel);

        // Insert the divider before the right panel
        if (rightPanel) {
            this.insertBefore(divider, rightPanel);
        }
    }
}

customElements.define('left-panel', LeftPanel);
customElements.define('right-panel', RightPanel);
customElements.define('panel-divider', PanelDivider);
customElements.define('panel-container', PanelContainer);
