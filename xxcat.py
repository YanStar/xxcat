import sys          # 导入sys模块，可以提供一些方便使用的操作系统函数的方法
import socket       # 导入socket模块
import getopt       # 导入getopt模块，专门用来处理命令行参数
import threading    # 导入线程模块
import subprocess   # 导入subprocess模块，与系统进行交互


# 定义一些全局变量
listen              = False
command             = False
upload              = False
execute             = ""
target              = ""
upload_destination  = ""
port                = 0


# 运行接收到的命令并且返回输出结果
def run_command(command):
    # 换行
    command = command.rstrip()

    # 运行命令并将输出返回
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except:
        output = "Failed to execute command.\r\n"

    # 将输出发送
    return output


# 将接收到的客户端套接字对象进行处理
def client_handler(client_socket):
    global upload
    global execute
    global command

    # 检测是否是上传文件
    if len(upload_destination):

        # 读取所有的字符并且写下目标
        file_buffer = ""

        # 持续读取数据直到没有符合的数据
        while True:
            data = client_socket.recv(1024)

            if not data:
                break
            else:
                file_buffer += data

        # 接收这些数据并将它们写出来
        try:
            file_descriptor = open(upload_destination, "wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()

            # 确认文件已经写出来了
            client_socket.send("Successfully saved file to %s\r\n" % upload_destination)
        except:
            client_socket.send("Failed to save file to %s\r\n" % upload_destination)

    # 检查命令执行
    if len(execute):
        # 运行命令
        output = run_command(execute)

        client_socket.send(output)

    # 如果需要一个命令行shell，那么将进入另一个循环
    if command:

        while True:
            # 跳出一个窗口
            client_socket.send("<XXCAT:#> ")

            # 开始接收数据直到发现换行符
            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)

            # 调用之前的ru_command函数并且将执行结果返回
            response = run_command(cmd_buffer)

            # 返回响应数据
            client_socket.send(response)


# 服务端程序
def server_loop():
    global target
    global port

    # 如果没有定义目标，我们将监听所有的接口
    if not len(target):
        target = "0.0.0.0"
    # 创建一个流式socket，TCP并绑定监听的地址和端口
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))

    # 开始监听TCP传入连接，默认连接数为5
    server.listen(5)

    # 让服务端进入主循环，在这里等待连接，当与一个客户端建立连接的时候，将接收到的客户端套接字对象保存到client_socket变量中，将远程连接的细节保存到addr变量中，然后以client_handler函数为回调函数创建一个新的线程对象
    while True:
        client_socket, addr = server.accept()
        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()


# 如果我们不进行监听，仅仅是个客户端程序
def client_sender(buffer):
    # 建立一个socket对象，服务器之间网络通信，TCP
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 连接到目标主机
        client.connect((target, port))

        #当发送的数据buffer存在则发送

        if len(buffer):
            client.send(buffer)

        while True:

            # 现在等待数据回传
            recv_len = 1
            response = ""

            while recv_len:
                data = client.recv(4096)
                recv_len = len(data)
                response += data

                if recv_len < 4096:
                    break

            print(response, )

            # 等待更多的输入
            buffer = input("")
            buffer += "\n"

            # 发送出去
            client.send(buffer)


    except:
        # 当出错时候，打印提示信息
        print("[*] Exception! Exiting.")

        # 关闭连接
        client.close()

# 定义一个使用帮助函数
def usage():
    print("Xx Net Tool")
    print()
    print("Usage: xxcat.py -t target_host -p port")
    print("-l --listen                - listen on [host]:[port] for incoming connections")
    print("-e --execute=file_to_run   - execute the given file upon receiving a connection")
    print("-c --command               - initialize a command shell")
    print("-u --upload=destination    - upon receiving connection upload a file and write to [destination]")
    print()
    print()
    print("Examples: ")
    print("bhpnet.py -t 192.168.0.1 -p 5555 -l -c")
    print("bhpnet.py -t 192.168.0.1 -p 5555 -l -u=c:\\target.exe")
    print("bhpnet.py -t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\"")
    print("echo 'ABCDEFGHI' | ./bhpnet.py -t 192.168.11.12 -p 135")
    sys.exit(0)


def main():
    # 定义一些全局变量
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):       # 从程序外部获取参数，sys.argv其实可以看作是一个列表，所以才能用[]提取其中的元素。其第一个元素是程序本身，随后才依次是外部给予的参数
        usage()

    # 读取命令行选项
    try:
        '''
            调用getopt函数。函数返回两个列表：opts和args。opts为分析出的格式信息。
            args为不属于格式信息的剩余的命令行参数,即不是按照getopt(）里面定义的长或短选项字符和附加参数以外的信息。
            opts是一个两元组的列表。每个元素为：(选项串,附加参数)。如果没有附加参数则为空串
            例如：
                python test.py -h -o file --help --output=out file1 file2
            则：
                opts的输出结果为：
                    [('-h', ''), ('-o', 'file'), ('--help', ''), ('--output', 'out')]

                而args则为：
                    ['file1', 'file2']，这就是上面不属于格式信息的剩余的命令行参数。
            
            函数一般使用：
                getopt(args, shortopts, longopts = [])
                参数args一般是sys.argv[1:]
                shortopts  短格式 (-) 
                longopts 长格式(--)
                所有的令行参数以空格为分隔符，都保存在了args列表中。其中第1个为脚本的文件名
            选项的写法要求：
                对于短格式，"-"号后面要紧跟一个选项字母。如果还有此选项的附加参数，可以用空格分开，也可以不分开。长度任意，可以用引号。如以下是正确的：
                    -o
                    -oa
                    -obbbb
                    -o bbbb
                    -o "a b"
　　             对于长格式，"--"号后面要跟一个单词。如果还有些选项的附加参数，后面要紧跟"="，再加上参数。"="号前后不能有空格。如以下是正确的：

                    --help=file1
                短格式中：
                    当一个选项只是表示开关状态时，即后面不带附加参数时，在分析串中写入选项字符。当选项后面是带一个附加参数时，在分析串中写入选项字符同时后面加一个":"号。
                    例如：
                        短格式分析串："ho:"代表"h"是一个开关选项；"o:"则表示后面应该带一个参数
                长格式中：
                    长格式串也可以有开关状态，即后面不跟"="号。如果跟一个等号则表示后面还应有一个参数
                    例如：
                        长格式分析串列表：["help", "output="]代表"help"是一个开关选项；"output="则表示后面应该带一个参数
            
        '''
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu:",["help", "listen", "execute", "target", "port", "command", "upload"])

        # 当运行出错时打印出错信息并且调用使用帮助函数
    except getopt.GetoptError as err:
        print(str(err))
        usage()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
        elif o in ("-e", "--execute"):
            execute = a
        elif o in ("-c", "--commandshell"):
            command = True
        elif o in ("-u", "--upload"):
            upload_destination = a
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert False, "Unhandled Option"        # 断言此处出错误

    # 判断是进行监听还是仅从标准输入发送数据
    if not listen and len(target) and port > 0:
        # 从命令行中读取数据
        buffer = sys.stdin.read()

        # 发送数据
        client_sender(buffer)

    # 当listen选项为True时我们开始监听并且准备上传文件、执行命令等操作，执行server_loop函数
    if listen:
        server_loop()


# 执行主程序
main()
