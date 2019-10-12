from cv import UIMatcher
from util import *
import uiautomator2 as u2
import random




class Automator:
    def __init__(self, device: str, upgrade_list: list, harvest_filter: list, is_args_list: dict):
        """
        device: 如果是 USB 连接，则为 adb devices 的返回结果；如果是模拟器，则为模拟器的控制 URL.
        """
        self.d = u2.connect(device)
        self.dWidth, self.dHeight = self.d.window_size()
        print(self.dWidth, self.dHeight)

        self.upgrade_list = upgrade_list
        self.harvest_filter = harvest_filter
        self.is_auto_policy = is_args_list["policy"]
        self.is_auto_task = is_args_list["task"]
        self.is_auto_train = is_args_list["train"]
        self.is_auto_upgrade = is_args_list["upgrade"]
        self.is_auto_collect = is_args_list["collect"]
        self.is_speedup = is_args_list["speed_up"]

        self.appRunning = False

    def start(self):
        """
        启动脚本，请确保已进入游戏页面。
        """
        self.train_count = 0 # 统计火车供货次数
        self.running_count = 0 # 记录执行次数
        while True:
            # 判断jgm进程是否在前台, 最多等待20秒，否则唤醒到前台
            if self.d.app_wait("com.tencent.jgm", front=True, timeout=20):
                if not self.appRunning:
                    # 从后台换到前台，留一点反应时间
                    print("[%s] App is front. JGM agent start in 3 seconds." % time.asctime())
                    time.sleep(3) 
                self.appRunning = True
            else:
                self.d.app_start("com.tencent.jgm")
                self.appRunning = False
                continue

            # 简单粗暴的方式，处理 “XX之光” 的荣誉显示。不管它出不出现，每次都点一下 确定 所在的位置
            self.d.click(550/1080, 1650/1920)

            # 升级政策
            if self.is_auto_policy:
                print("[%s] Checking policy..." % time.asctime())
                self.check_policy()

            # 完成城市任务
            if self.is_auto_task:
                print("[%s] Checking task..." % time.asctime())
                self.check_task()

            # 处理火车供货
            if self.is_auto_train:
                print("[%s] Checking train..." % time.asctime())
                self.check_train()

            # 升级建筑
            if self.is_auto_upgrade:
                print("[%s] Upgrading buildings..." % time.asctime())
                self.upgrade(self.upgrade_list)

            # 收金币
            if self.is_auto_collect:
                print("[%s] Collecting coins..." % time.asctime())
                self.collect_coins()

            time.sleep(2)
            self.running_count += 1
            print("[%s] Running count: %d." % (time.asctime(), self.running_count))
            print("[%s] -------------------------------" % time.asctime())


    def check_policy(self):
        # 看看政策中心那里有没有冒绿色箭头气泡
        if len(UIMatcher.findGreenArrow(self.d.screenshot(format="opencv"))):
            # 打开政策中心
            self.d.click(0.206, 0.097)
            time.sleep(0.5)
            # 确认升级
            self.d.click(0.077, 0.122)
            # 拉到顶
            self._slide_to_top()
            # 开始找绿色箭头,找不到就往下滑,最多划5次
            for i in range(5):
                screen = self.d.screenshot(format="opencv")
                arrows = UIMatcher.findGreenArrow(screen)
                if len(arrows):
                    x,y = arrows[0]
                    self.d.click(x,y) # 点击这个政策
                    short_wait()
                    self.d.click(0.511, 0.614) # 确认升级
                    print("[%s] --- Policy upgraded! ---" % time.asctime())
                    self._back_to_main()

                    return
                # 如果还没出现绿色箭头，往下划
                self.d.swipe(0.482, 0.809, 0.491, 0.516, duration = 0.3)
            self._back_to_main()

    def check_task(self):
        # 看看任务中心有没有冒黄色气泡
        screen = self.d.screenshot(format="opencv")
        if UIMatcher.findTaskBubble(screen):
            self.d.click(0.16, 0.84) # 打开城市任务
            short_wait()
            self.d.click(0.51, 0.819) # 点击 完成任务
            print("[%s] --- Task finished! ---" % time.asctime())
            self._back_to_main()

    def check_train(self):
        good_id = self._has_good()
        if len(good_id) == 3:
            print("[%s] The train is coming with %d gonds." % (time.asctime(), len(good_id)))
            self.harvest(self.harvest_filter, good_id)
            self.train_count += 1
            print("[%s] Trains count: %d." % (time.asctime(), self.train_count))
        else:
            # print("[%s] No Train."%time.asctime())
            findSomething = True

        # 再看看是不是有货没收，如果有就重启app
        good_id = self._has_good()
        if len(good_id) > 0 and self.is_speedup:
            self.d.app_stop("com.tencent.jgm")
            print("[%s] The train is coming with %d gonds. Resetting app..." % (time.asctime(), len(good_id)))
            # 重新启动app
            self.d.app_start("com.tencent.jgm")
            time.sleep(15)

    def upgrade(self, upgrade_list):
        if not len(upgrade_list):
            return
        self._open_upgrade_interface()
        building,count = random.choice(upgrade_list)
        self._upgrade_one_with_count(building,count) 
        self._close_upgrade_interface()
    
    def collect_coins(self):
        try:
            for i in range(3):
                # 横向滑动，共 3 次。
                sx, sy = BUILDING_POSITIONS[i * 3 + 1]
                ex, ey = BUILDING_POSITIONS[i * 3 + 3]
                self.d.swipe(sx-0.1, sy+0.05, ex, ey)
            # for i in [1, 2, 3, 6, 5, 4, 7, 8, 9]:
            #     x, y = BUILDING_POSITIONS[i]
            #     self.d.click(x, y)
        except(Exception):
            # 用户在操作手机，暂停10秒
            time.sleep(10)

    def harvest(self, building_filter, goods:list):
        '''
        新的傻瓜搬货物方法,先按住截图判断绿光探测货物目的地,再搬
        '''
        short_wait()
        for good in goods:
            pos_id = self.guess_good(good)
            if pos_id != 0 and pos_id in building_filter:
                # 搬5次
                self._move_good_by_id(good, BUILDING_POSITIONS[pos_id], times=4)
                # short_wait()

    def guess_good(self, good_id):
        '''
        按住货物，探测绿光出现的位置
        这一段应该用numpy来实现，奈何我对numpy不熟。。。
        '''
        diff_screens = self.get_screenshot_while_touching(GOODS_POSITIONS[good_id]) 
        return UIMatcher.findGreenLight(diff_screens)

    def get_screenshot_while_touching(self, location, pressed_time=0.2):
        '''
        Get screenshot with screen touched.
        '''
        screen_before = self.d.screenshot(format="opencv")
        h,w = len(screen_before),len(screen_before[0])
        x,y = (location[0] * w,location[1] *h)
        # 按下
        self.d.touch.down(x,y)
        # print('[%s]Tapped'%time.asctime())
        time.sleep(pressed_time)
        # 截图
        screen = self.d.screenshot(format="opencv")
        # print('[%s]Screenning'%time.asctime())
        # 松开
        self.d.touch.up(x,y)
        # 返回按下前后两幅图
        return screen_before, screen

    def _open_upgrade_interface(self):
        screen = self.d.screenshot(format="opencv")
        # 判断升级按钮的颜色，蓝比红多就处于正常界面，反之在升级界面
        R, G, B = UIMatcher.getPixel(screen,0.974,0.615)
        if B > R:
            self.d.click(0.9, 0.57)

    def _close_upgrade_interface(self):
        screen = self.d.screenshot(format="opencv")
        # 判断升级按钮的颜色，蓝比红多就处于正常界面，反之在升级界面
        R, G, B = UIMatcher.getPixel(screen,0.974,0.615)
        if B < R:
            self.d.click(0.9, 0.57)

    def _upgrade_one_with_count(self,id,count):
        sx, sy=BUILDING_POSITIONS[id]
        self.d.click(sx, sy)
        time.sleep(0.3)
        for i in range(count):
            self.d.click(0.798, 0.884)
            # time.sleep(0.1)
       
    def _move_good_by_id(self, good: int, source, times=1):
        try:
            sx, sy = GOODS_POSITIONS[good]
            ex, ey = source
            for i in range(times):
                self.d.drag(sx, sy, ex, ey, duration = 0.1)
                short_wait()
        except(Exception):
            pass    

    def _has_good(self):
        '''
        返回有货的位置列表
        '''
        screen = self.d.screenshot(format="opencv")  
        return UIMatcher.detectCross(screen)

    def _slide_to_top(self):
        for i in range(3):
            self.d.swipe(0.488, 0.302,0.482, 0.822)
            short_wait()

    def _back_to_main(self):
        for i in range(3):
            self.d.click(0.057, 0.919)
            short_wait()
