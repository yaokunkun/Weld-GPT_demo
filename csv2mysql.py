import csv
import argparse

def csv_to_param_data_insert(csv_file, output_file=None):
    """
    将CSV文件转换为param_data表的MySQL INSERT语句
    """
    # 定义表名和字段顺序（与CSV列顺序一致）
    table_name = "param_data"
    fields = ["Material", "Thickness", "Method", "ParamName", "ParamValue", "Diameter"]
    
    # 生成INSERT语句前缀
    # 为字段名添加反引号，避免与关键字冲突
    quoted_fields = [f"`{field}`" for field in fields]
    insert_prefix = f"INSERT INTO `{table_name}` ({', '.join(quoted_fields)}) VALUES "
    
    # 读取CSV文件并处理
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        
        # 验证表头是否匹配
        header = next(reader)
        if header != fields:
            raise ValueError(f"CSV表头与表结构不匹配。预期: {fields}，实际: {header}")
        
        values_clauses = []
        row_count = 0
        
        # 处理每一行数据
        for row in reader:
            row_count += 1
            # 处理每个字段值
            values = []
            for value in row:
                # 转义单引号
                escaped_value = value.replace("'", "''")
                # 空值处理为NULL
                if escaped_value.strip() == '':
                    values.append('NULL')
                else:
                    values.append(f"'{escaped_value}'")
            
            values_clauses.append(f"({', '.join(values)})")
            
            # 每1000行生成一个INSERT语句，避免语句过长
            if len(values_clauses) >= 1000:
                sql = insert_prefix + ', '.join(values_clauses) + ';'
                write_or_print(sql, output_file)
                values_clauses = []
        
        # 处理剩余的行
        if values_clauses:
            sql = insert_prefix + ', '.join(values_clauses) + ';'
            write_or_print(sql, output_file)
    
    print(f"转换完成！共处理了 {row_count} 条记录。")

def write_or_print(content, output_file):
    """将内容写入文件或打印到控制台"""
    if output_file:
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(content + '\n')
    else:
        print(content)

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='将CSV文件转换为param_data表的MySQL INSERT语句')
    parser.add_argument('--csv_file', help='CSV文件路径')
    parser.add_argument('--output', help='输出SQL文件路径')
    
    args = parser.parse_args()
    
    # 如果指定了输出文件，先清空文件
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            pass
    
    # 执行转换
    try:
        csv_to_param_data_insert(args.csv_file, args.output)
    except Exception as e:
        print(f"转换失败: {str(e)}")
