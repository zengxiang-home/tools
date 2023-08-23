import argparse
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from PIL import Image, ImageDraw, ImageFont

## pre process for txt file 
def pre_process_for_txt_file(file_path):
    # 读取文件并备份内容
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # 处理每一行
    with open(file_path, 'w', encoding='utf-8') as file:
        for line in lines:
            # 如果一行全部是空格，则忽略
            if line.strip() == '':
                continue

            # 替换空格为'.'
            modified_line = line.replace(' ', '.')
            file.write(modified_line)

# 读取文本文件内容
def process_txt_to_image(input_filename):
    with open(input_filename, 'r') as f:
        lines = f.readlines()

    first_valid_raw = 1
    for idx, line in enumerate(lines, start=1):
        if line.strip() and all(char in ['.', 'A', 'X', 'x', 'S', '1', '2', '6'] for char in line.strip()):
            first_valid_raw = int((idx - 1) / 2)
            # print("============" + str(first_valid_raw))   ## TODO_ZENGXIANG: find a feature to diff old 2 txt && 3 new txt
            break

    color_mapping = {
        ' ': (255, 255, 255),
        '.': (255, 255, 255),  # 白色
        'A': (0, 255, 0),     # 绿色
        'X': (255, 0, 0),     # 红色
        'x': (255, 0, 0),
        'S': (0, 0, 255),
        '1': (255, 255, 0),
        '2': (255, 255, 0),
        '6': (255, 255, 0),
    }


    # 去除每行末尾的换行符
    lines = [line.strip() for line in lines]

    # 创建新图像
    image_height = len([line for line in lines if line]) * 40  # 只计算非空行的高度，每行对应一个40x40的方框
    max_line_length = max(len(line) for line in lines if line)
    image_width = max_line_length * 40  # 每个字符对应一个40x40的方框

    image = Image.new('RGB', (image_width, image_height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()  # 使用默认字体

    # 绘制方框、字符和坐标
    y = 0
    for line in lines:
        if line:
            x = 0
            has_special_char = False
            for idx, char in enumerate(line):
                if char in color_mapping:
                    color = color_mapping[char]
                    draw.rectangle([x, y, x + 40, y + 40], fill=color, outline=(0, 0, 0))
                    char_width, char_height = draw.textsize(char, font=font)
                    draw.text((x + (40 - char_width) // 2, y + (40 - char_height) // 2), char, fill=(0, 0, 0), font=font)
                    draw.text((x, y + 5), f"({idx+1},{y//40+1 - first_valid_raw})", fill=(0, 0, 0), font=font)
                else:
                    has_special_char = True
                    break
                x += 40

            if has_special_char:
                draw.text((x + 5, y + 5), line, fill=(0, 0, 0), font=font)
                y += 40
            else:
                y += 40

    # 保存图像
    output_filename = input_filename.replace('txt', 'png')
    image.save(output_filename)
    print("图像已保存为: " + output_filename)

# read excel file context
def process_excel_to_image(input_filename, opr):

    df = pd.read_excel(input_filename, skiprows=11) 
    # 读取Excel数据
    df = pd.read_excel(input_filename)

    # 提取数据列
    x_values = df['X']
    y_values = df['Y']
    operation_list = ['Rdson_RT (Ω)', 'Vth_RT (V)', 'Igss_RT (A)', 'Idss_RT (A)']
    rdson_values = df[operation_list[int(opr)]]

    rdson_norm = Normalize(vmin=min(rdson_values), vmax=max(rdson_values))

    # 创建子图
    fig, ax = plt.subplots(figsize=(8, 6))

    for x, y, rdson in zip(x_values, y_values, rdson_values):
        rect = plt.Rectangle((x - 0.5, y - 0.5), 1, 1, linewidth=1, edgecolor='black', facecolor=plt.cm.viridis(rdson_norm(rdson)))
        ax.add_patch(rect)

    # 添加颜色标注
    sm = plt.cm.ScalarMappable(cmap='viridis', norm=plt.Normalize(vmin=min(rdson_values), vmax=max(rdson_values)))
    sm.set_array([])  # 设置一个空的数组，仅为了绘制颜色标注
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label('Rdson_RT  (Ω)')

    # 设置坐标轴范围
    ax.set_xlim(min(x_values) - 0.5, max(x_values) + 0.5)
    ax.set_ylim(min(y_values) - 0.5, max(y_values) + 0.5)

    # 添加标题和坐标轴标签
    plt.title('Rectangles Plot of Rdson_RT')
    plt.xlabel('X')
    plt.ylabel('Y')

    # 保存图像
    output_filename = input_filename.replace('excel', 'png')
    output_filename = output_filename.replace('xlsx', 'png') 
    output_filename = output_filename.replace('.png', operation_list[int(opr)]+'.png') 
    plt.savefig(output_filename)
    print("图像已保存为: " + output_filename)


def main():
    parser = argparse.ArgumentParser(description="Convert test file to image")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-m", type=int, choices=[1, 2], help="Mode: 1 for convert txt to png, 2 for convert excel to png")

    parser.add_argument("-i", help="Path to the folder containing txt files.")
    parser.add_argument("-o", help="dump diff value to png(0-Rdson_RT (Ω); 1-Vth_RT (V); 2-Igss_RT (A); 3-Idss_RT (A)).")

    
    args = parser.parse_args()
    txt_path = args.i
    operation = args.o
    input_filename = os.listdir(txt_path)

    mode = args.m

    if mode == 1:
        for file_name in input_filename:
            absolute_path = os.path.join(txt_path, file_name)
            pre_process_for_txt_file(txt_path + "/" + file_name)
            process_txt_to_image(txt_path + "/" + file_name)
    elif mode == 2:
        for file_name in input_filename:
            absolute_path = os.path.join(txt_path, file_name)
            process_excel_to_image(txt_path + "/" + file_name, operation)

if __name__ == "__main__":
    main()
























