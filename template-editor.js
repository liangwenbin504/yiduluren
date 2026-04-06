/**
 * 模板编辑模块
 * 用于编辑导入的模板数据
 */

// 全局模板编辑模块对象
const TemplateEditor = {
    /**
     * 打开模板编辑界面
     * @param {Object} templateData - 模板数据
     * @param {Function} callback - 编辑完成后的回调函数
     */
    openTemplateEditor(templateData, callback) {
        console.log('📄 打开模板编辑界面:', templateData);
        
        // 创建编辑界面
        const editorModal = this.createEditorModal(templateData, callback);
        document.body.appendChild(editorModal);
        
        // 显示编辑界面
        setTimeout(() => {
            editorModal.classList.add('show');
        }, 100);
    },
    
    /**
     * 创建编辑界面
     * @param {Object} templateData - 模板数据
     * @param {Function} callback - 编辑完成后的回调函数
     * @returns {HTMLElement} 编辑界面元素
     */
    createEditorModal(templateData, callback) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-window">
                <div class="modal-header">
                    <h2 class="modal-title">编辑模板</h2>
                    <button class="modal-close" id="templateEditorClose">&times;</button>
                </div>
                <div class="modal-content">
                    <form id="templateEditorForm">
                        <!-- 基本信息 -->
                        <div class="filter-group">
                            <label class="filter-label">标题类型</label>
                            <input type="text" class="filter-input" id="templateTitleType" value="${templateData.title_type || '择日課單'}" placeholder="请输入标题类型">
                        </div>
                        
                        <div class="filter-group">
                            <label class="filter-label">坐山</label>
                            <input type="text" class="filter-input" id="templateMountain" value="${templateData.mountain || ''}" placeholder="请输入坐山">
                        </div>
                        
                        <div class="filter-group">
                            <label class="filter-label">向山</label>
                            <input type="text" class="filter-input" id="templateXiangshan" value="${templateData.xiangshan || ''}" placeholder="请输入向山">
                        </div>
                        
                        <!-- 四柱信息 -->
                        <div class="filter-group">
                            <label class="filter-label">四柱信息</label>
                            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;">
                                <input type="text" class="filter-input" id="templateYear" value="${templateData.four_pillars?.year || '年柱'}" placeholder="年柱">
                                <input type="text" class="filter-input" id="templateMonth" value="${templateData.four_pillars?.month || '月柱'}" placeholder="月柱">
                                <input type="text" class="filter-input" id="templateDay" value="${templateData.four_pillars?.day || '日柱'}" placeholder="日柱">
                                <input type="text" class="filter-input" id="templateHour" value="${templateData.four_pillars?.hour || '时柱'}" placeholder="时柱">
                            </div>
                        </div>
                        
                        <!-- 六壬数据 -->
                        <div class="filter-group">
                            <label class="filter-label">六壬数据</label>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                                <input type="text" class="filter-input" id="templateYueJiang" value="${templateData.daliuren_data?.yueJiang || '月将'}" placeholder="月将">
                                <input type="text" class="filter-input" id="templateShiChen" value="${templateData.daliuren_data?.shiChen || '时辰'}" placeholder="时辰">
                            </div>
                        </div>
                        
                        <!-- 评价内容 -->
                        <div class="filter-group">
                            <label class="filter-label">断语内容</label>
                            <textarea class="filter-input" id="templateEvaluation" rows="5" placeholder="请输入断语内容">${templateData.evaluation || '断语内容'}</textarea>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button class="btn-modal btn-cancel" id="templateEditorCancel">取消</button>
                    <button class="btn-modal btn-confirm" id="templateEditorSave">保存</button>
                </div>
            </div>
        `;
        
        // 绑定事件
        modal.querySelector('#templateEditorClose').addEventListener('click', () => {
            this.closeEditorModal(modal);
        });
        
        modal.querySelector('#templateEditorCancel').addEventListener('click', () => {
            this.closeEditorModal(modal);
        });
        
        modal.querySelector('#templateEditorSave').addEventListener('click', () => {
            const editedData = this.collectEditedData(modal, templateData);
            callback(editedData);
            this.closeEditorModal(modal);
        });
        
        // 点击外部关闭
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeEditorModal(modal);
            }
        });
        
        return modal;
    },
    
    /**
     * 关闭编辑界面
     * @param {HTMLElement} modal - 编辑界面元素
     */
    closeEditorModal(modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(modal);
        }, 300);
    },
    
    /**
     * 收集编辑后的数据
     * @param {HTMLElement} modal - 编辑界面元素
     * @param {Object} originalData - 原始模板数据
     * @returns {Object} 编辑后的数据
     */
    collectEditedData(modal, originalData) {
        return {
            title_type: modal.querySelector('#templateTitleType').value,
            mountain: modal.querySelector('#templateMountain').value,
            xiangshan: modal.querySelector('#templateXiangshan').value,
            four_pillars: {
                year: modal.querySelector('#templateYear').value,
                month: modal.querySelector('#templateMonth').value,
                day: modal.querySelector('#templateDay').value,
                hour: modal.querySelector('#templateHour').value
            },
            daliuren_data: {
                yueJiang: modal.querySelector('#templateYueJiang').value,
                shiChen: modal.querySelector('#templateShiChen').value,
                tianPan: originalData.daliuren_data?.tianPan || {},
                sike: originalData.daliuren_data?.sike || [
                    { top: '上神', bottom: '下神', guiren: '贵人' },
                    { top: '上神', bottom: '下神', guiren: '贵人' },
                    { top: '上神', bottom: '下神', guiren: '贵人' },
                    { top: '上神', bottom: '下神', guiren: '贵人' }
                ],
                sanchuan: originalData.daliuren_data?.sanchuan || {
                    '初传': { tiangan: '天干', dizhi: '地支', liuqin: '六亲', guiren: '贵人' },
                    '中传': { tiangan: '天干', dizhi: '地支', liuqin: '六亲', guiren: '贵人' },
                    '末传': { tiangan: '天干', dizhi: '地支', liuqin: '六亲', guiren: '贵人' }
                }
            },
            dates: originalData.dates || [
                { date: '日期', hour: '时辰', score: '评分' }
            ],
            keti_list: originalData.keti_list || [],
            evaluation: modal.querySelector('#templateEvaluation').value
        };
    },
    
    /**
     * 保存模板数据到文件
     * @param {Object} templateData - 模板数据
     * @param {string} filename - 文件名
     */
    saveTemplateToFile(templateData, filename = 'template.json') {
        const dataStr = JSON.stringify(templateData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const a = document.createElement('a');
        a.href = URL.createObjectURL(dataBlob);
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        console.log('📄 模板保存成功:', filename);
    }
};
