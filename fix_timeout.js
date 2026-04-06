// 在浏览器控制台中运行此代码以修复超时问题
// 按 F12 打开控制台，粘贴并运行

(function() {
    console.log('🔧 正在修复日期分析 API 调用...');
    
    // 保存原始的 fetchApi 函数
    const originalFetchApi = window.fetchApi;
    
    // 包装 fetchApi 函数，增加超时时间
    window.fetchApi = function(url, options = {}) {
        // 如果是日期分析 API，使用更长的超时时间
        if (url && url.includes('/doushou/full_range_analyze')) {
            console.log('🚀 检测到日期分析 API 调用，使用 120 秒超时');
            options.timeout = 120000; // 120 秒超时
        }
        
        return originalFetchApi.call(this, url, options);
    };
    
    console.log('✅ 修复完成！日期分析 API 现在使用 120 秒超时');
    console.log('💡 提示：刷新页面后会失效，需要重新运行此代码');
})();
