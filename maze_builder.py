
path=r'C:\Users\hanan\OneDrive\Desktop\game\mazes'
file=r'maze_level_1.csv'
def read_maze(maze_file):
    with open(maze_file, 'r') as f:
        maze_string=f.read()
        sep_maze_string= maze_string.split('\n')
        return sep_maze_string
maze_lines=read_maze(path+'\\'+file)
game_object_list=[]
for y_counter,line in enumerate(maze_lines):
    x_counter=0
    line=line.split(' ')
    print(line)
    for char in line:
        if char=='w':
            game_object_list.append(Wall())
        x_counter=x_counter+1
