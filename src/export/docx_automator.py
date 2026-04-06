"""
文档处理自动化模块
实现文档格式重新设计、导入和生成的自动化流程
"""

from .docx_formatter import DocxFormatter
from .docx_exporter import LiuRenExporter
import os


class DocxAutomator:
    """DOCX 文档处理自动化"""
    
    def __init__(self):
        """初始化文档处理自动化"""
        self.formatter = DocxFormatter()
        self.exporter = LiuRenExporter()
    
    def auto_process(self, input_file=None, output_file=None, template_name=None, result_data=None):
        """
        自动化处理流程
        :param input_file: 输入文档路径（可选）
        :param output_file: 输出文档路径
        :param template_name: 模板名称（可选）
        :param result_data: 六壬排盘结果数据（可选）
        :return: 是否处理成功
        """
        try:
            if input_file and os.path.exists(input_file):
                # 导入现有文档并应用格式
                doc = self.formatter.import_document(input_file)
                if doc:
                    # 加载模板（如果指定）
                    if template_name:
                        self.formatter.load_template(template_name)
                    
                    # 应用格式
                    self.formatter.apply_format(doc)
                    
                    # 导出文档
                    if output_file:
                        return self.formatter.export_document(doc, output_file)
            elif result_data:
                # 基于数据生成新文档
                doc = self.formatter.generate_document(result_data, template_name)
                if doc and output_file:
                    return self.formatter.export_document(doc, output_file)
            return False
        except Exception as e:
            print(f"自动化处理失败: {e}")
            return False
    
    def batch_process(self, input_dir, output_dir, template_name=None):
        """
        批量处理文档
        :param input_dir: 输入目录
        :param output_dir: 输出目录
        :param template_name: 模板名称
        :return: 处理成功的文件数
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        success_count = 0
        for file in os.listdir(input_dir):
            if file.endswith('.docx'):
                input_file = os.path.join(input_dir, file)
                output_file = os.path.join(output_dir, file)
                if self.auto_process(input_file, output_file, template_name):
                    success_count += 1
        return success_count
    
    def create_template_from_document(self, input_file, template_name):
        """
        从现有文档创建模板
        :param input_file: 输入文档路径
        :param template_name: 模板名称
        :return: 是否创建成功
        """
        try:
            # 导入文档
            doc = self.formatter.import_document(input_file)
            if not doc:
                return False
            
            # 提取文档格式信息（这里简化处理，实际需要更复杂的提取逻辑）
            # 目前使用默认格式，可以根据需要扩展
            
            # 保存为模板
            return self.formatter.save_template(template_name)
        except Exception as e:
            print(f"创建模板失败: {e}")
            return False
    
    def list_available_templates(self):
        """
        列出所有可用模板
        :return: 模板名称列表
        """
        return self.formatter.list_templates()
    
    def update_template(self, template_name, format_dict):
        """
        更新模板
        :param template_name: 模板名称
        :param format_dict: 格式设置字典
        :return: 是否更新成功
        """
        try:
            # 加载模板
            if not self.formatter.load_template(template_name):
                return False
            
            # 更新格式
            self.formatter.update_format(format_dict)
            
            # 保存模板
            return self.formatter.save_template(template_name)
        except Exception as e:
            print(f"更新模板失败: {e}")
            return False
