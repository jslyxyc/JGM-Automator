from automator import Automator
import subprocess

if __name__ == '__main__':
    # 升级建筑列表, 实际升级是随机从这个列表中挑一个升级, 为空不升级
    # up_list = [(1,5),(2,5),(3,5),(4,5),(5,5),(6,5),(7,5),(8,5),(9,5)]  # 雨露均沾
    # up_list = [(1,1),(1,1),(1,1),(4,3)] # 75%的概率1号升级1次， 25%的概率4号升级3次
    # up_list = [(8,1),(9,1)] # 这个号建筑升级1次， 那个号建筑升级1次
    up_list = []

    # 收货过滤列表
    harvest_filter = [1,2,3,4,5,6,7,8,9] # 收取这些号建筑的货物

    # 参数设置列表
    args_list = {
        "album": 0, # 相册
        "policy": False, # 是否自动升级政策
        "task": False, # 是否自动完成城市任务
        "upgrade": False, # 是否自动升级建筑
        "train": False, # 是否自动处理火车供货
        "speed_up": 3, # 火车小于多少就自动重启加速刷火车
        "collect": True, # 是否自动收金币
    }

    # adb设备列表
    adb_devices = {
        "Device1": 'QV7039V30X',
        "Device2": 'CB512BC4ZL',
        "Device1Net": '10.21.20.105',
        "Device2Net": '10.21.59.70',
        "MuMu": '127.0.0.1:7555'
    }

    if b'connected' in subprocess.check_output('adb connect '+ adb_devices["MuMu"]):
        print("Successfully connected to MuMu.")
    instance = Automator(adb_devices["MuMu"], up_list, harvest_filter, args_list)

    # 启动脚本
    instance.start()

    # TODO & FIXME
    # 树莓派移植
    # 政策和城市任务只在没有火车时检测（优先级）
    # 收货间隔时间太长 
    # 完成城市任务后不收金币
    # 流水线、多线程
    # 应用启动至前台，The train is coming with 3 gonds.
