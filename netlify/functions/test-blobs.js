exports.handler = async function(event, context) {
    let result = {};
    try {
        const { getStore } = require("@netlify/blobs");
        result.getStoreType = typeof getStore;
        result.env_keys = Object.keys(process.env).filter(k => k.toLowerCase().includes("blob") || k.toLowerCase().includes("netlify"));
        
        const store = getStore("buyers");
        await store.set("test_key", "test_val");
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
