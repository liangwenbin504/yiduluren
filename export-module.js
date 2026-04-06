/**
 * 文档导出模块
 * 包含完整的文档导出逻辑、格式处理及错误处理机制
 */

// API基础URL
// 使用全局API_BASE_URL或默认值
if (typeof window.API_BASE_URL === 'undefined') {
    window.API_BASE_URL = 'http://localhost:5000/api';
}

// 确保API_BASE_URL变量可用
const EXPORT_API_BASE_URL = window.API_BASE_URL;

// 全局导出模块对象
const ExportModule = {
    /**
     * 导出文档
     * @param {Object} exportData - 导出数据
     * @param {string} format - 导出格式，可选值：'docx' 或 'ppt'
     * @returns {Promise<Object>} 导出结果
     */
    async exportDocument(exportData, format = 'docx') {
        try {
            console.log(`📄 开始导出${format.toUpperCase()}文档...`);
            console.log('📄 导出数据:', exportData);
            
            // 直接使用不同的端点
            let endpoint;
            if (format === 'ppt') {
                // 使用专门的PPT导出端点
                endpoint = '/ppt-export';
            } else {
                endpoint = '/export/docx';
            }
            
            console.log(`📄 调用API端点: ${EXPORT_API_BASE_URL}${endpoint}`);
            
            const response = await fetch(`${EXPORT_API_BASE_URL}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(exportData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            console.log('📄 导出结果:', result);
            
            if (result.success) {
                // 下载文件
                let filename = result.filename;
                // 如果是PPT格式，确保文件扩展名是.pptx
                if (format === 'ppt') {
                    // 不管API返回什么扩展名，都强制使用.pptx
                    filename = filename.replace(/\.[^.]+$/, '.pptx');
                }
                // 确保使用正确的下载端点
                const downloadUrl = `${EXPORT_API_BASE_URL}/export/download/${result.filename}`;
                console.log(`📄 下载URL: ${downloadUrl}`);
                console.log(`📄 下载文件名: ${filename}`);
                
                // 使用更可靠的下载方法
                try {
                    // 先获取文件内容
                    const fileResponse = await fetch(downloadUrl);
                    if (!fileResponse.ok) {
                        throw new Error('下载文件失败');
                    }
                    
                    // 创建Blob URL
                    const blob = await fileResponse.blob();
                    const blobUrl = window.URL.createObjectURL(blob);
                    
                    // 创建下载链接
                    const a = document.createElement('a');
                    a.href = blobUrl;
                    a.download = filename;
                    document.body.appendChild(a);
                    
                    // 稍微延迟一下再点击，确保浏览器有时间处理
                    setTimeout(() => {
                        a.click();
                        // 清理
                        setTimeout(() => {
                            document.body.removeChild(a);
                            window.URL.revokeObjectURL(blobUrl);
                        }, 100);
                    }, 50);
                } catch (downloadError) {
                    console.error('📄 下载文件失败:', downloadError);
                    // 降级方案：使用原始方法
                    const a = document.createElement('a');
                    a.href = downloadUrl;
                    a.download = filename;
                    a.target = '_blank';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                }
                
                return {
                    success: true,
                    message: `✅ ${format.toUpperCase()}文档导出成功！\n文件：${filename}\n\n文档已使用模板格式保存为标准的 ${format} 格式。`,
                    filename: filename
                };
            } else {
                throw new Error(result.error || '未知错误');
            }
        } catch (error) {
            console.error(`❌ 导出${format.toUpperCase()}文档失败:`, error);
            return {
                success: false,
                message: `❌ 导出${format.toUpperCase()}文档失败：${error.message}\n\n请确保 API 服务器正在运行。`
            };
        }
    },
    
    /**
     * 导出PPT文档
     * @param {Object} exportData - 导出数据
     * @returns {Promise<Object>} 导出结果
     */
    async exportPptDocument(exportData) {
        // 添加模板路径到导出数据
        if (this.currentTemplatePath) {
            exportData.template_path = this.currentTemplatePath;
            console.log('📄 使用模板路径:', this.currentTemplatePath);
        }
        return this.exportDocument(exportData, 'ppt');
    },
    
    /**
     * 设置当前模板路径
     * @param {string} templatePath - 模板文件路径
     */
    setCurrentTemplate(templatePath) {
        this.currentTemplatePath = templatePath;
        console.log('📄 当前模板路径已设置:', templatePath);
    },
    
    /**
     * 导出模板
     * @param {string} format - 模板格式，可选值：'docx' 或 'ppt'
     * @returns {Promise<Object>} 导出结果
     */
    async exportTemplate(format = 'docx') {
        try {
            console.log(`📄 开始导出${format.toUpperCase()}模板...`);
            
            // 生成模板数据
            const templateData = {
                title_type: '择日課單',
                mountain: '',
                xiangshan: '',
                four_pillars: {
                    year: '年柱',
                    month: '月柱',
                    day: '日柱',
                    hour: '时柱'
                },
                daliuren_data: {
                    yueJiang: '月将',
                    shiChen: '时辰',
                    tianPan: {},
                    sike: [
                        { top: '上神', bottom: '下神', guiren: '贵人' },
                        { top: '上神', bottom: '下神', guiren: '贵人' },
                        { top: '上神', bottom: '下神', guiren: '贵人' },
                        { top: '上神', bottom: '下神', guiren: '贵人' }
                    ],
                    sanchuan: {
                        '初传': { tiangan: '天干', dizhi: '地支', liuqin: '六亲', guiren: '贵人' },
                        '中传': { tiangan: '天干', dizhi: '地支', liuqin: '六亲', guiren: '贵人' },
                        '末传': { tiangan: '天干', dizhi: '地支', liuqin: '六亲', guiren: '贵人' }
                    }
                },
                dates: [
                    { date: '日期', hour: '时辰', score: '评分' }
                ],
                keti_list: [],
                evaluation: '断语内容'
            };
            
            // 根据格式选择不同的API端点
            const endpoint = format === 'ppt' ? '/ppt-export' : '/export/docx';
            
            const response = await fetch(`${EXPORT_API_BASE_URL}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(templateData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            console.log(`📄 ${format.toUpperCase()}模板导出结果:`, result);
            
            if (result.success) {
                // 下载文件
                const downloadUrl = `${EXPORT_API_BASE_URL}/export/download/${result.filename}`;
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = `模板_${result.filename}`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                
                return {
                    success: true,
                    message: `✅ ${format.toUpperCase()}模板导出成功！\n文件：模板_${result.filename}\n\n可用于后续导入使用。`,
                    filename: result.filename
                };
            } else {
                throw new Error(result.error || '未知错误');
            }
        } catch (error) {
            console.error(`❌ 导出${format.toUpperCase()}模板失败:`, error);
            return {
                success: false,
                message: `❌ 导出${format.toUpperCase()}模板失败：${error.message}\n\n请确保 API 服务器正在运行。`
            };
        }
    },
    
    /**
     * 导入模板
     * @param {File} file - 模板文件
     * @returns {Promise<Object>} 导入结果
     */
    async importTemplate(file) {
        try {
            console.log('📄 开始导入模板...');
            console.log('📄 导入文件:', file.name);
            console.log('📄 文件类型:', file.type);
            
            // 检查文件类型
            const fileExtension = file.name.split('.').pop().toLowerCase();
            
            // 支持PPT和JSON格式的模板文件
            if (!['pptx', 'json'].includes(fileExtension)) {
                return {
                    success: false,
                    message: `❌ 只支持PPTX和JSON格式的模板文件，当前文件格式: ${fileExtension}`
                };
            }
            
            // 处理PPTX文件
            if (fileExtension === 'pptx') {
                return await this.importPptTemplate(file);
            }
            
            // 处理JSON文件
            const reader = new FileReader();
            
            return new Promise((resolve, reject) => {
                reader.onload = async (e) => {
                    try {
                        const content = e.target.result;
                        const templateData = JSON.parse(content);
                        
                        console.log('📄 模板数据解析成功:', templateData);
                        
                        // 验证模板数据格式
                        if (!templateData.title_type || !templateData.four_pillars) {
                            throw new Error('模板格式错误，缺少必要字段');
                        }
                        
                        resolve({
                            success: true,
                            message: '✅ 模板导入成功！',
                            data: templateData
                        });
                    } catch (error) {
                        console.error('❌ 解析模板文件失败:', error);
                        reject({
                            success: false,
                            message: `❌ 解析模板文件失败：${error.message}`
                        });
                    }
                };
                
                reader.onerror = () => {
                    console.error('❌ 读取文件失败');
                    reject({
                        success: false,
                        message: '❌ 读取文件失败'
                    });
                };
                
                reader.readAsText(file);
            });
        } catch (error) {
            console.error('❌ 导入模板失败:', error);
            return {
                success: false,
                message: `❌ 导入模板失败：${error.message}`
            };
        }
    },
    
    /**
     * 导入PPT模板
     * @param {File} file - PPT模板文件
     * @returns {Promise<Object>} 导入结果
     */
    async importPptTemplate(file) {
        try {
            console.log('📄 开始导入PPT模板...');
            
            // 创建FormData对象
            const formData = new FormData();
            formData.append('template', file);
            
            // 调用后端API导入PPT模板
            const apiUrl = `${EXPORT_API_BASE_URL}/import/ppt-template`;
            console.log('📄 调用API URL:', apiUrl);
            const response = await fetch(apiUrl, {
                method: 'POST',
                body: formData
            });
            console.log('📄 API响应状态:', response.status);
            console.log('📄 API响应状态文本:', response.statusText);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            console.log('📄 PPT模板导入结果:', result);
            
            if (result.success) {
                return {
                    success: true,
                    message: '✅ PPT模板导入成功！',
                    data: result.data,
                    template_path: result.template_path
                };
            } else {
                throw new Error(result.error || '未知错误');
            }
        } catch (error) {
            console.error('❌ 导入PPT模板失败:', error);
            return {
                success: false,
                message: `❌ 导入PPT模板失败：${error.message}`
            };
        }
    },
    
    /**
     * 收集导出数据
     * @returns {Object} 导出数据
     */
    collectExportData() {
        const shanxiangEl = document.getElementById('shanxiang');
        const shanxiangValue = shanxiangEl ? shanxiangEl.value : '';
        const zetiriTypeSelectEl = document.getElementById('zetiriTypeSelect');
        const zetiriTypeValue = zetiriTypeSelectEl ? zetiriTypeSelectEl.value : '';
        
        const yearPillarEl = document.getElementById('yearPillar');
        const monthPillarEl = document.getElementById('monthPillar');
        const dayPillarEl = document.getElementById('dayPillar');
        const hourPillarEl = document.getElementById('hourPillar');
        
        const aiEvaluationEl = document.getElementById('aiEvaluation');
        
        const dateListEl = document.getElementById('dateList');
        const dateItems = dateListEl ? dateListEl.querySelectorAll('.date-item') : [];
        
        const yearPillar = yearPillarEl ? yearPillarEl.textContent : '--';
        const monthPillar = monthPillarEl ? monthPillarEl.textContent : '--';
        const dayPillar = dayPillarEl ? dayPillarEl.textContent : '--';
        const hourPillar = hourPillarEl ? hourPillarEl.textContent : '--';
        
        const titleType = zetiriTypeValue === '安葬' ? '安葬吉日' : 
                        zetiriTypeValue === '立碑' ? '立碑吉日' :
                        zetiriTypeValue === '婚嫁' ? '婚嫁吉日' : '擇日課單';
        
        const shanxiangParts = shanxiangValue ? shanxiangValue.split('山') : ['', ''];
        const zuoshan = shanxiangParts[0] || '';
        const xiangshan = shanxiangParts[1] ? shanxiangParts[1].replace('向', '') : '';
        
        // 收集六壬数据（天地盘、四课、三传）
        const daliurenData = {
            yueJiang: document.getElementById('yuejiangShichenInfo')?.textContent?.match(/月将：([^\s（]+)/)?.[1] || '--',
            shiChen: document.getElementById('yuejiangShichenInfo')?.textContent?.match(/时辰：([^\s]+)/)?.[1] || '--',
            tianPan: {},
            sike: [],
            sanchuan: {}
        };
        
        // 收集天盘数据
        const tiandiGrid = document.getElementById('tiandiGrid');
        if (tiandiGrid) {
            const tiandiCells = tiandiGrid.querySelectorAll('.tiandi-cell:not(.placeholder)');
            tiandiCells.forEach(cell => {
                const zhi = cell.querySelector('div > div:first-child')?.textContent;
                if (zhi) {
                    daliurenData.tianPan[zhi] = zhi;
                }
            });
        }
        
        // 收集四课数据
        for (let i = 1; i <= 4; i++) {
            const topEl = document.getElementById(`sicol${i}Top`);
            const bottomEl = document.getElementById(`sicol${i}Bottom`);
            const guirenEl = document.getElementById(`sicol${i}Guiren`);
            if (topEl && bottomEl) {
                daliurenData.sike.push({
                    top: topEl.textContent || '--',
                    bottom: bottomEl.textContent || '--',
                    guiren: guirenEl?.textContent || ''
                });
            }
        }
        
        // 收集三传数据
        const chuanNames = ['chuanchu', 'zhongchuan', 'mochuan'];
        const chuanLabels = ['初传', '中传', '末传'];
        chuanNames.forEach((name, i) => {
            const tianganEl = document.getElementById(`${name}Rigan`);
            const dizhiEl = document.getElementById(`${name}Dizhi`);
            const liuqinEl = document.getElementById(`${name}Liuqin`);
            const guirenEl = document.getElementById(`${name}Guiren`);
            if (tianganEl && dizhiEl) {
                daliurenData.sanchuan[chuanLabels[i]] = {
                    tiangan: tianganEl.textContent || '--',
                    dizhi: dizhiEl.textContent || '--',
                    liuqin: liuqinEl?.textContent || '',
                    guiren: guirenEl?.textContent || ''
                };
            }
        });
        
        // 准备导出数据
        const exportData = {
            title_type: titleType,
            mountain: zuoshan,
            xiangshan: xiangshan,
            four_pillars: {
                year: yearPillar,
                month: monthPillar,
                day: dayPillar,
                hour: hourPillar
            },
            daliuren_data: daliurenData,
            dates: [],
            keti_list: [],  // 课格列表
            // 使用 innerText 保留换行和格式，确保断语库内容完整
            evaluation: aiEvaluationEl ? aiEvaluationEl.innerText : ''
        };
        
        // 从 AI 评价中提取课格信息（如果有）
        const aiEvalText = aiEvaluationEl ? aiEvaluationEl.textContent : '';
        if (aiEvalText.includes('元首课')) exportData.keti_list.push('元首课');
        if (aiEvalText.includes('重审课')) exportData.keti_list.push('重审课');
        if (aiEvalText.includes('知一课')) exportData.keti_list.push('知一课');
        if (aiEvalText.includes('龙德课')) exportData.keti_list.push('龙德课');
        if (aiEvalText.includes('福德课')) exportData.keti_list.push('福德课');
        if (aiEvalText.includes('旺相课')) exportData.keti_list.push('旺相课');
        if (aiEvalText.includes('比和课')) exportData.keti_list.push('比和课');
        if (aiEvalText.includes('贵人课')) exportData.keti_list.push('贵人课');
        if (aiEvalText.includes('禄马课')) exportData.keti_list.push('禄马课');
        
        console.log('📋 课格列表:', exportData.keti_list);
        
        // 收集日期数据
        if (dateItems.length > 0) {
            dateItems.forEach((item) => {
                const date = item.dataset.date || '--';
                const hour = item.dataset.hour || '--';
                const score = item.dataset.score || '--';
                exportData.dates.push({
                    date: date,
                    hour: hour,
                    score: score
                });
            });
        }
        
        console.log('📄 导出文档数据:', exportData);
        return exportData;
    }
};
