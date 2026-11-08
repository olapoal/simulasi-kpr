exports.handler = async function(event, context) {
    let result = {};
    try {
        const { getStore, connectLambda } = require("@netlify/blobs");
        result.hasConnectLambda = typeof connectLambda;
        if (typeof connectLambda === "function") {
            connectLambda(event);
        }
        
        result.event_keys = Object.keys(event);
        result.blobs_in_event = !!event.blobs;
        
        const store = getStore("buyers");
        await store.set("test_key", "test_val_ok");
        const val = await store.get("test_key");
        result.success = true;
        result.val = val;
    } catch (err) {
        result.success = false;
        result.error_name = err.name;
        result.error_message = err.message;
        result.error_stack = err.stack;
    }
    return {
        statusCode: 200,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(result, null, 2)
    };
};
