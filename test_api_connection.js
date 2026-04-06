// 测试API连接的脚本
const API_BASE_URL = 'http://localhost:5000/api';

async function testAPIConnection() {
    console.log('开始测试API连接...');
    
    try {
        // 测试大六壬排盘API
        const response = await fetch(`${API_BASE_URL}/daliuren/paipan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                tianGan: '甲',
                diZhi: '子',
                yueJiang: '亥',
                shiZhi: '子'
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP错误! 状态码: ${response.status}`);
        }

        const result = await response.json();
        console.log('API响应结果:', result);

        if (result.success) {
            console.log('✅ API连接成功！');
            console.log('月将:', result.data.yueJiang);
            console.log('时辰:', result.data.shiChen);
            console.log('天地盘:', result.data.tianPan);
            console.log('四课:', result.data.siKe);
            console.log('三传:', result.data.sanChuan);
        } else {
            console.log('❌ API返回错误:', result.error);
        }
    } catch (error) {
        console.log('❌ 测试失败:', error.message);
    }
}

// 运行测试
testAPIConnection();
