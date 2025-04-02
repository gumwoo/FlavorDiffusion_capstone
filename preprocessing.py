import csv
import argparse, sys

parser = argparse.ArgumentParser()
parser.add_argument('-file', help='set input file name')
args = parser.parse_args()

# 향미성분 csv 파일에서 compound_name이 존재하는 행의 인덱스
COMPOUND_NAME = 3

input_file = ''
node_file = 'dataset/nodes_191120.csv'
edge_file = 'dataset/edges_191120.csv'

def add_to_nodes(id, name, node_type):
    with open(node_file, 'a') as node_f:
        node_writer = csv.writer(node_f)

        fourth_arg = ''
        if node_type == 'compound':                 # type이 compound면 무조건 food compound가 되도록 정해둠. (임시)
            arg = 'food'
            fourth_arg = arg
        elif node_type == 'ingredient':             # type이 ingredient면 무조건 no_hub가 되도독 정해둠. (임시)
            arg = 'no_hub'
            fourth_arg = arg

        new_node = [id, name, '', node_type, fourth_arg]
        node_writer.writerow(new_node)                          # add to node csv file

        print(f"node added: ", new_node)
        return new_node


def find_from_nodes(name, node_type):
    with open(node_file, 'r') as node_f:
        node_contents = csv.reader(node_f)
        next(node_contents)

        id_count = 0
        for row in node_contents:
            if row[1] == name:
                print(f"found node: ", row)
                return row                      # return result
            id_count = id_count + 1

        new_node = add_to_nodes(id_count, name, node_type)      # 모든 노드를 검색해도 일치하는 결과가 없으면, 새로 추가
        return new_node


def find_node_type(node):
    if node[3] == 'ingredient':     return 'ingr'
    elif node[3] == 'compound':

        if node[4] == 'food':       return 'fcomp'
        elif node[4] == 'drug':     return 'dcomp'


def add_to_edges(node_1, node_2):
    with open(edge_file, 'a') as edge_f:
        edge_writer = csv.writer(edge_f)

        node_1_type = find_node_type(node_1)                    # 엣지 csv 파일 양식에 맞도록
        node_2_type = find_node_type(node_2)                    # 노드 별 타입 문자열 변경

        edge_type = ''                                          # determine edge type경

        # 엣지의 방향 상관없이 ingr가 앞으로 오도록 작성함.
        if node_1_type == 'ingr':
            new_edge_type = node_1_type + '-' + node_2_type
            edge_type = new_edge_type
        elif node_2_type == 'ingr':
            new_edge_type = node_2_type + '-' + node_1_type
            edge_type = new_edge_type

        new_edge = [node_1[0], node_2[0], '', edge_type]        # 엣지 간 스코어는 일단 공백으로 설정함.
        edge_writer.writerow(new_edge)                          # add to edge csv file

        print(f"edge added: ", new_edge)
        return new_edge


def find_from_edges(node_1, node_2):
    with open(edge_file, 'r') as edge_f:
        edge_contents = csv.reader(edge_f)
        next(edge_contents)

        for row in edge_contents:                      # 엣지 방향에 상관없이 검색함.
            if (row[0] == node_1 and row[1] == node_2) or \
                (row[0] == node_2 and row[1] == node_1):
                    print(f"found edge: ", row)
                    return row

        new_edge = add_to_edges(node_1, node_2)         # 모든 엣지를 검색해도 일치하는 결과가 없으면, 새로 추가
        return new_edge

def main(argv, args):
    input_file = args.file
    with open(input_file, 'r') as input_f:
        input_contents = csv.reader(input_f)

        # 술의 이름을 alcohol_name_list에 저장한다.
        alcohol_name_list = []                          # store alcohol's name
        for i in range(0, 3):
            next(input_contents)

        first_flag = True                               # alcohol_name_list에 술 이름을 저장하기 위한 플래그
        for row in input_contents:
            if first_flag == True:
                for name in row:
                    if name != '':  alcohol_name_list.append(name.replace(' ', ''))       # 문자열 전처리

                first_flag = False                      # 최초 1회 시행 이후 위 if문은 수행하지 않는다.
                continue

            name = row[COMPOUND_NAME].strip().replace(' ', '_').lower()   # 공백을 언더바(_)로 대체, 알파벳 소문자로 변경
            if name != '':
                node_1 = find_from_nodes(name, 'compound')                   # 노드 검색

            concentration_list = row[5:len(row)]
            for i in range(0, len(concentration_list) - 5):
                if concentration_list[i] != '':
                    name = alcohol_name_list[i]
                    node_2 = find_from_nodes(name, 'ingredient')        # 노드 검색

                    find_from_edges(node_1, node_2)                     # 엣지 검색

if __name__ == '__main__':
    argv = sys.argv
    main(argv, args)
