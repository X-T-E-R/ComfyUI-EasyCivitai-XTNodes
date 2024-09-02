import { app } from "../../../scripts/app.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";

// Displays input text on a node
app.registerExtension({
	name: "XTNodes.ShowText",
	async beforeRegisterNodeDef(nodeType, nodeData, app) {
		const validNodeNames = [
			"CheckpointLoaderSimpleWithPreviews",
			"LoraLoaderWithPreviews",
			"LoraLoaderStackedWithPreviews",
			"LoraLoaderStackedAdvancedWithPreviews",
			"CivitaiCheckpointLoaderSimple",
			"CivitaiLoraLoader",
			"CivitaiLoraLoaderStacked",
			"CivitaiLoraLoaderStackedAdvanced",
			"XTNodesCleanPrompt",
    		"XTNodesPromptConcatenate"
		];

		if (validNodeNames.includes(nodeData.name)) {
			console.log("Valid node name found:", nodeData.name);

			// When the node is executed we will be sent the input text, display this in the widget
			const onExecuted = nodeType.prototype.onExecuted;
			nodeType.prototype.onExecuted = function (message) {
				console.log("Node executed, message received:", message);

				onExecuted?.apply(this, arguments);

				if (this.widgets) {
					const pos = this.widgets.findIndex((w) => w.name === "text");
					if (pos !== -1) {
						for (let i = pos; i < this.widgets.length; i++) {
							this.widgets[i].onRemove?.();
						}
						this.widgets.length = pos;
					}
				}

				for (const list of message.text) {
					const w = ComfyWidgets["STRING"](this, "text", ["STRING", { multiline: true }], app).widget;
					w.inputEl.readOnly = true;
					w.inputEl.style.opacity = 0.6;
					w.value = list;
				}

				this.onResize?.(this.size);
			};
		}
	},
});
