"""剧本：《Cheems规则怪谈：月光宠物旅馆》（原创）。

每一场（Scene）由若干拍（beat）组成：
  L  台词（谁说、说什么、表情、音效、语音特效）
  P  停顿 / 动作
  Card 时间卡（「凌晨 1:00」之类）
台词时长由配音实际长度决定，画面按拍的起止时间来安排动作。
"""
from __future__ import annotations

# 角色 → 百炼千问 TTS 音色（qwen3-tts-flash 系统音色）
VOICES = {
    "narr": "Andre",       # 旁白：磁性沉稳
    "rules": "Seren",      # 守则：舒缓、平静得有点瘆人
    "cheems": "Nofish",    # Cheems：男 · 不卷舌
    "cat": "Katerina",     # 大橘：御姐
    "husky": "Dylan",      # 二哈：北京话
    "corgi": "Bella",      # 小柯：童声
    "zhuang": "Vincent",   # 大壮：烟嗓豪迈
    "golden": "Eldric Sage",  # 老金：沉稳长者
    "owner": "Ethan",      # 主人
    "parrot": "Momo",      # 阿福：俏皮
    "thief": "Ryan",       # 偷狗贼：戏剧张力
    "staff": "Maia",       # 王店长
    "mom": "Serena",       # 鹦鹉学的小柯妈妈
    "husky_mimic": "Dylan",
    "owner_mimic": "Ethan",
    "hidden": "Ryan",      # 纸条（其实是偷狗贼的声音）
    "devil": "Nofish",
    "angel": "Nofish",
}

# 语速调整（不变调加速）：有些音色天生说得慢
TEMPO = {"golden": 1.35, "rules": 1.12, "cat": 1.08, "corgi": 1.08, "zhuang": 1.06, "hidden": 1.08}

# 字幕上的名字
NAMES = {
    "narr": "", "rules": "守则", "cheems": "Cheems", "cat": "大橘", "husky": "二哈", "corgi": "小柯",
    "zhuang": "大壮", "golden": "老金", "owner": "主人", "parrot": "阿福", "thief": "偷狗贼",
    "staff": "王店长", "mom": "？？？", "husky_mimic": "？？？", "owner_mimic": "？？？", "hidden": "纸条",
    "devil": "小恶魔Cheems", "angel": "小天使Cheems",
}

# 语音特效（默认）
DEFAULT_FX = {
    "mom": "mimic", "husky_mimic": "mimic", "owner_mimic": "mimic", "hidden": "whisper",
    "devil": "devil", "angel": "angel",
}

# 嘴型对应到画面上的哪个角色
MOUTH_OF = {"husky_mimic": "parrot", "owner_mimic": "parrot", "mom": "parrot", "devil": "devil",
            "angel": "angel"}


class L:
    def __init__(self, who, text, id=None, emo=None, gap=0.32, fx=None, sfx=(), sub=None, vol=1.0, pre=0.0, speed=None):
        self.who = who
        self.speed = speed
        self.text = text
        self.id = id
        self.emo = emo or {}
        self.gap = gap
        self.fx = fx if fx is not None else DEFAULT_FX.get(who)
        self.sfx = list(sfx)
        self.sub = text if sub is None else sub
        self.vol = vol
        self.pre = pre

    kind = "line"


class P:
    def __init__(self, dur, id=None, sfx=(), emo=None):
        self.dur = dur
        self.id = id
        self.sfx = list(sfx)
        self.emo = emo or {}

    kind = "pause"


class Card:
    def __init__(self, text, sub="", dur=2.8, id=None, sfx=(("clock_chime", 0.1, 0.8),)):
        self.text = text
        self.sub = sub
        self.dur = dur
        self.id = id
        self.sfx = list(sfx)
        self.emo = {}

    kind = "card"


class Scene:
    def __init__(self, name, beats, music=None, amb=None, music_gain=1.0):
        self.name = name
        self.beats = beats
        self.music = music
        self.amb = amb
        self.music_gain = music_gain


SCENES = [
    # ------------------------------------------------------------ 冷开场
    Scene("cold_open", [
        P(1.2, "dark", sfx=[("drone_hit", 0.0, 0.7)]),
        L("rules", "欢迎入住月光宠物旅馆。为了您的安全，请务必遵守以下守则。", "r0", gap=0.7,
          sfx=[("paper", 0.0, 0.8)]),
        L("rules", "第七条：本守则，全部为真。", "r7", gap=0.9),
        P(0.6, "glitch", sfx=[("glitch", 0.0, 0.8)]),
        P(4.6, "title", sfx=[("title_hit", 0.0, 1.0)]),
    ], music="cold", amb="room_tone"),

    # ------------------------------------------------------------ 旅馆门口
    Scene("drop_off", [
        L("narr", "Cheems是一只普通的柴犬。胆子小，饭量大。最大的爱好是吃，第二大的爱好，是想着吃。", "n1",
          emo={"cheems": "hungry"}),
        L("narr", "这天，主人要出差三天，只好把它送到了城郊的月光宠物旅馆。", "n2", emo={"cheems": "normal"}),
        L("owner", "Cheems，我就出差三天。三天后的早上，我一定来接你。", "o1"),
        L("cheems", "主人不要走m……我会想你的m……", "c1", emo={"cheems": "weep"}),
        L("owner", "乖。你看，这是你最喜欢的红色牵引绳。我把它带在身上，来接你的时候，第一件事就是给你系上，好不好？",
          "o2", emo={"cheems": "sad"}),
        L("cheems", "那……拉钩m。", "c2", emo={"cheems": "happy"}, sfx=[("sparkle", 0.9, 0.7)]),
        P(3.2, "leave", sfx=[("steps_soft", 0.6, 0.5)], emo={"cheems": "sad"}),
        L("cheems", "主人……要早点回来m……", "c3", emo={"cheems": "weep"}),
    ], music="day", amb="birds"),

    # ------------------------------------------------------------ 大堂登记
    Scene("lobby", [
        L("narr", "旅馆的大堂很安静。前台上趴着一只橘猫，脖子上挂着一块小金牌：夜班管理员。", "n3",
          sfx=[("door_bell", 0.2, 0.7)]),
        L("cat", "新来的？登记一下喵。叫什么名字？", "k1", emo={"cat": "lazy", "cheems": "nervous"}),
        L("cheems", "Cheems。", "c4"),
        L("parrot", "Cheems！Cheems！欢迎光临！欢迎光临！", "p1", sfx=[("wings", 0.0, 0.6)],
          emo={"cheems": "shock"}),
        L("cheems", "哇，它会学我说话m！", "c5", emo={"cheems": "sparkle"}),
        L("parrot", "乖！我一定来接你！我一定来接你！", "p2"),
        L("cat", "那是阿福，前两天住进来的鹦鹉，听见什么学什么，别理它。", "k2", emo={"cheems": "normal"}),
        L("cat", "记住，晚上十点熄灯。你房间的饭碗底下压着一份守则，睡觉前一定要看喵。", "k3"),
        L("cheems", "宠物旅馆……还有守则m？", "c6", emo={"cheems": "confused"}),
        L("cat", "有的狗看了守则，第二天平平安安地回家了。", "k4", emo={"cat": "creepy"}),
        L("cat", "没看的……也回家了。只不过，是被别人带回家的喵。", "k5", emo={"cheems": "scared"},
          sfx=[("sting_soft", 0.0, 0.6)]),
        P(3.4, "photo", sfx=[("gulp", 0.2, 0.9)]),
    ], music="lobby", amb="room_tone"),

    # ------------------------------------------------------------ 走廊认识邻居
    Scene("corridor_day", [
        L("narr", "管理员带着Cheems穿过走廊。走廊两边是五间客房，每扇门的下面，都有一个只够狗狗钻出去的小门洞。", "n4"),
        L("corgi", "你……你好，我叫小柯。我想妈妈了……妈妈说，明天一早就来接我。", "g1",
          emo={"corgi": "weep", "cheems": "normal"}),
        L("cheems", "别怕m，睡一觉，妈妈就来了m。", "c7", emo={"cheems": "happy", "corgi": "normal"}),
        L("zhuang", "九十八，九十九，一百！兄弟，练过吗？", "z1", emo={"zhuang": "cool", "cheems": "shock"}),
        L("cheems", "我……我只练过吃饭m。", "c8", emo={"cheems": "nervous"}),
        L("zhuang", "哈哈哈！记住，男子汉，只吃蛋白质！这旅馆的狗粮太素了，晚上我得溜出去找点肉吃。", "z2",
          emo={"zhuang": "happy", "cheems": "normal"}),
        L("cat", "到了，三号房，就是你的。", "k6", emo={"cat": "lazy"}),
        L("husky", "嗷呜——新邻居！新邻居来啦！哥们儿你叫啥？", "h1", emo={"husky": "derp", "cheems": "shock"},
          sfx=[("door_bang", 0.0, 0.8)]),
        L("cheems", "我、我叫Cheems。", "c9", emo={"cheems": "nervous"}),
        L("husky", "芝士？好名儿啊，闻着就香！得嘞，以后我就叫你芝士了！芝士！芝士！", "h2"),
        L("cheems", "是Cheems m……", "c10", emo={"cheems": "sad"}),
        L("husky", "知道了芝士！", "h3"),
        L("golden", "新来的孩子？", "j1", emo={"cheems": "normal", "golden": "normal"}),
        L("cheems", "老爷爷好m，您也是来寄养的吗m？", "c11", emo={"cheems": "happy"}),
        L("golden", "嗯。我在这里，住了很久很久了。", "j2", emo={"cheems": "normal"}),
        L("cheems", "多久m？", "c12", emo={"cheems": "confused"}),
        L("golden", "久到……我已经快想不起来，主人长什么样子了。", "j3", emo={"golden": "sad", "cheems": "sad"}),
        L("golden", "孩子，晚上不管听到什么，都别出门。", "j4", emo={"golden": "normal"}),
        L("cat", "晚安喵。", "k7", gap=0.8),
    ], music="lobby", amb="room_tone"),

    # ------------------------------------------------------------ 22:00 守则
    Scene("rules", [
        Card("22:00", "熄灯"),
        L("narr", "晚上十点，灯灭了。Cheems饿着肚子，想把饭碗再舔一遍，却在碗底下，发现了一张折起来的纸。", "n5",
          emo={"cheems": "hungry"}, sfx=[("lights_off", 0.0, 0.8), ("paper", 6.5, 0.8)]),
        L("rules", "月光宠物旅馆，夜间住客守则。", "r_t", emo={"cheems": "normal"}, gap=0.5),
        L("rules", "一、晚上十点以后，请待在自己的房间里。走廊里，不会有任何住客。", "r1", gap=0.6),
        L("rules", "二、本旅馆只有一位夜班管理员，是一只橘猫。如果你同时看到两只橘猫，请立刻闭上眼睛，数到十。", "r2",
          gap=0.6),
        L("rules", "三、凌晨两点会送夜宵，夜宵只有狗粮。如果你闻到了肉骨头的香味，不要吃，那不是给你的。", "r3",
          gap=0.6),
        L("rules", "四、凌晨三点，隔壁的哈士奇可能会叫你的名字。不要回答。哈士奇不知道你的名字。", "r4", gap=0.6),
        L("rules", "五、天亮以后，如果主人来接你，请先看他手里有没有牵引绳。没有牵引绳的，不是你的主人。", "r5",
          gap=0.6),
        L("rules", "六、天亮之前，不要照镜子。", "r6", gap=0.6),
        L("rules", "七、本守则，全部为真。", "r7b", gap=1.0, sfx=[("sting_soft", 0.0, 0.7)]),
        L("cheems", "这……这到底是宠物旅馆，还是鬼屋m？", "c13", emo={"cheems": "scared"}),
        L("cheems", "没事的m……只要遵守守则，睡一觉，天就亮了m。", "c14", emo={"cheems": "nervous"},
          sfx=[("blanket", 2.2, 0.8)]),
        P(1.0, "hide"),
    ], music="night", amb="night_room"),

    # ------------------------------------------------------------ 23:00 小柯
    Scene("corgi_cry", [
        Card("23:00"),
        L("corgi", "呜呜……妈妈……我想回家……", "g2", fx="vent", emo={"cheems": "worried"}),
        L("cheems", "小柯？别哭m。我给你讲个笑话m。", "c15", emo={"cheems": "normal"}),
        L("cheems", "从前有一只柴犬，它特别爱吃。有一天，它把自己的尾巴当成了甜甜圈，追着咬了一整天m。", "c16",
          emo={"cheems": "happy"}),
        L("corgi", "噗……哥哥，那只柴犬是你吧？", "g3", fx="vent"),
        L("cheems", "……不是m。", "c17", emo={"cheems": "guilty"}, gap=0.8),
        L("corgi", "嘿嘿。哥哥，你害怕吗？", "g4", fx="vent", emo={"cheems": "normal"}),
        L("cheems", "我、我才不怕m。", "c18", emo={"cheems": "nervous"}, sfx=[("teeth", 0.9, 0.7)], gap=0.9),
    ], music="night", amb="night_room"),

    # ------------------------------------------------------------ 00:00 走廊里的影子
    Scene("shadow", [
        Card("00:00"),
        L("narr", "午夜十二点，走廊里传来了脚步声。", "n6", sfx=[("steps_heavy", 0.0, 0.9)]),
        L("cheems", "守则第一条：走廊里不会有任何住客m……那、那外面走路的，是什么m？", "c19",
          emo={"cheems": "scared"}),
        P(2.6, "pass", sfx=[("steps_heavy", 0.0, 0.8), ("sting", 1.6, 0.9)]),
        L("zhuang", "兄弟，还没睡啊？夜跑去不？", "z3", emo={"cheems": "terror", "zhuang": "happy"}),
        L("cheems", "大、大壮？守则说晚上不能出门的m！", "c20", emo={"cheems": "shock"}),
        L("zhuang", "守则？那都是吓唬小狗的！我天天晚上出来练，啥事没有。走了啊！", "z4",
          emo={"cheems": "worried"}),
        P(1.2, "jog", sfx=[("steps_heavy", 0.0, 0.6)]),
        L("narr", "Cheems松了一口气。可它忽然想到：如果守则全部为真，走廊里不会有任何住客……那刚才窗外的那个，真的是大壮吗？",
          "n7", emo={"cheems": "scared"}, sfx=[("sting_soft", 6.0, 0.7)]),
    ], music="night", amb="night_room"),

    # ------------------------------------------------------------ 01:00 两只橘猫
    Scene("two_cats", [
        Card("01:00"),
        L("cat", "还没睡喵？小孩子要早点睡。", "k8", sfx=[("bell_jingle", 0.0, 0.5), ("flashlight", 0.0, 0.6)],
          emo={"cheems": "nervous", "cat": "lazy"}),
        L("cheems", "管理员姐姐……我有点怕m……", "c21", emo={"cheems": "worried"}),
        L("cat", "怕就对了喵。会害怕的狗，才活得久。", "k9", emo={"cat": "creepy"}),
        P(2.4, "second", sfx=[("sting", 1.2, 1.0)]),
        L("cheems", "两……两只橘猫m！", "c22", emo={"cheems": "terror"}),
        P(0.6, "close"),
        L("cheems", "一m，二m，三m，四m，五m……", "count1", sfx=[("whir", 0.3, 0.7), ("heartbeat", 0.0, 0.8)]),
        L("cheems", "六m，七m，八m，九m……", "count2", sfx=[("hiss", 0.2, 0.8), ("thump", 1.4, 0.8),
                                                         ("heartbeat", 0.0, 0.8)]),
        L("cheems", "十m！", "count3", gap=0.5),
        P(0.9, "open", sfx=[("sting", 0.0, 0.9)]),
        L("cat", "好孩子。你很守规矩喵。", "k10", emo={"cat": "creepy", "cheems": "terror"}),
        P(1.2, "leave"),
        L("cheems", "刚才那个……是哪一只m……", "c23", emo={"cheems": "scared"}, gap=0.8),
    ], music="night2", amb="night_room"),

    # ------------------------------------------------------------ 02:00 肉骨头
    Scene("bone", [
        Card("02:00"),
        L("cat", "夜宵来了喵。", "k11", sfx=[("cart", 0.0, 0.7), ("bowl_slide", 1.2, 0.8)],
          emo={"cheems": "normal"}),
        L("cheems", "狗粮好干m……", "c24", emo={"cheems": "sad"}, sfx=[("crunch_small", 0.0, 0.6)]),
        P(2.0, "aroma", sfx=[("sniff", 0.8, 0.9)]),
        L("cheems", "这、这是……肉骨头的香味m！", "c25", emo={"cheems": "hungry"}),
        L("devil", "吃吧m，就一口m，守则又看不见m。", "d1", emo={"cheems": "hungry"}, sfx=[("poof", 0.0, 0.6)]),
        L("angel", "不行m！守则第三条：那不是给你的m！", "a1", sfx=[("poof", 0.0, 0.6)]),
        P(1.4, "growl", sfx=[("stomach", 0.0, 1.0)], emo={"cheems": "cry"}),
        L("cheems", "我好饿m……可是……我忍m！", "c26", emo={"cheems": "cry"}),
        P(0.6, "pillow"),
        L("zhuang", "嚯！夜宵加餐！这才叫蛋白质！嘎嘣脆！", "z5", fx="wall", emo={"cheems": "shock"},
          sfx=[("crunch", 1.0, 0.9)]),
        P(2.4, "silence", sfx=[("crunch", 0.0, 0.8), ("thud", 1.6, 0.9)]),
        L("cheems", "大壮？大壮你怎么不说话了m？", "c27", emo={"cheems": "worried"}),
        P(2.6, "drag", sfx=[("drag", 0.3, 0.6)], emo={"cheems": "scared"}),
    ], music="night", amb="night_room"),

    # ------------------------------------------------------------ 03:00 叫名字
    Scene("voices", [
        Card("03:00"),
        P(1.4, "wings", sfx=[("wings", 0.2, 0.6)]),
        L("mom", "小柯——小柯——妈妈来接你了——", "m1", emo={"cheems": "worried"}),
        L("corgi", "妈妈？是妈妈！", "g5", fx="vent", sfx=[("flap", 1.0, 0.7), ("patter", 1.2, 0.6)]),
        L("cheems", "小柯，别出去m！现在才三点m！", "c28", emo={"cheems": "shock"}),
        P(2.0, "gone"),
        L("cheems", "小柯？……小柯？", "c29", emo={"cheems": "worried"}, gap=1.0),
        L("husky_mimic", "Cheems……Cheems……开开门呀……我是二哈……", "hm1", emo={"cheems": "normal"}),
        L("cheems", "我在m——", "c30", emo={"cheems": "happy"}, gap=0.15),
        P(0.8, "cover", emo={"cheems": "shock"}),
        L("cheems", "不对m。守则说，哈士奇不知道你的名字……", "c31", emo={"cheems": "think"}),
        L("husky", "芝士！芝士！", "h4", fx="flashback", gap=1.0),
        L("cheems", "二哈从来没叫对过我的名字m，它一直叫我芝士m……那门外的……是谁m？", "c32",
          emo={"cheems": "scared"}),
        L("husky_mimic", "Cheems……开门呀……Cheems……", "hm2", sfx=[("scratch", 0.3, 0.8)],
          emo={"cheems": "terror"}),
        P(1.0, "hold"),
        L("husky", "呼……噜……芝士……鸡腿……给我留一个……呼……", "h5", fx="wall", sfx=[("snore", 0.0, 0.6)],
          emo={"cheems": "confused"}),
        P(1.8, "quiet", sfx=[("wings", 0.3, 0.5)]),
    ], music="night2", amb="night_room"),

    # ------------------------------------------------------------ 03:30 老金的纸条
    Scene("note", [
        Card("03:30"),
        L("golden", "孩子……你还醒着吗？", "j5", fx="vent", emo={"cheems": "shock"}),
        L("cheems", "老金爷爷！小柯和大壮都不见了m！", "c33", emo={"cheems": "cry"}),
        L("golden", "我知道。每隔几天，就会有狗在夜里消失。", "j6", fx="vent", emo={"cheems": "worried"}),
        L("golden", "孩子，你真的以为，那份守则是在保护你吗？", "j7", fx="vent"),
        P(1.4, "slide", sfx=[("paper", 0.3, 0.9)]),
        L("golden", "这是以前的住客偷偷留下的。你看看吧。", "j8", fx="vent"),
        L("hidden", "真正的规则。", "x0", gap=0.5),
        L("hidden", "一、墙上的守则是管理员写的。管理员，不是猫。", "x1", gap=0.6),
        L("hidden", "二、闻到肉骨头的香味，就说明又有一只狗，被它吃掉了。", "x2", gap=0.6),
        L("hidden", "三、天亮以后，主人来接你，一定要跟他走。不管他有没有带牵引绳。", "x3", gap=0.6),
        L("hidden", "四、想知道真相，就去走廊尽头的美容室，照一照镜子。", "x4", gap=0.9,
          sfx=[("sting_soft", 0.0, 0.7)]),
        L("cheems", "管理员……不是猫？那它是什么m？", "c34", emo={"cheems": "scared"}),
        L("golden", "我不知道。我只知道，留在这里的狗，就再也回不了家了。比如我。", "j9", fx="vent",
          emo={"cheems": "sad"}),
        L("cheems", "可是……守则第七条说，守则全部为真m……", "c35", emo={"cheems": "worried"}),
        L("golden", "那你就自己去看看吧。", "j10", fx="vent", gap=0.9),
    ], music="night", amb="night_room"),

    # ------------------------------------------------------------ 04:00 美容室的镜子
    Scene("mirror_walk", [
        Card("04:00"),
        L("narr", "Cheems做了一个它这辈子最勇敢的决定：去找小柯和大壮。", "n8",
          emo={"cheems": "determined"}),
        P(1.6, "squeeze", sfx=[("flap", 0.2, 0.8), ("pop", 1.1, 0.9)]),
        L("cheems", "我、我是一只勇敢的柴犬m……勇敢的柴犬不怕黑m……", "c36", emo={"cheems": "nervous"}),
        P(2.2, "walk1", sfx=[("steps_soft", 0.0, 0.4)]),
        L("cheems", "大壮的骨头……只啃了一半m。", "c37", emo={"cheems": "think"}),
        L("cheems", "这骨头的味道怪怪的m，有一股……药味m。", "c38", emo={"cheems": "worried"},
          sfx=[("sniff", 0.0, 0.8)]),
        P(3.0, "walk2", sfx=[("steps_soft", 0.0, 0.4), ("door_creak", 2.2, 0.7)]),
    ], music="tension", amb="night_room"),

    Scene("mirror", [
        L("cheems", "守则第六条：天亮之前，不要照镜子m……不看m，不看m……", "c39", emo={"cheems": "nervous"}),
        P(2.8, "peek", sfx=[("sting", 1.8, 1.0)]),
        L("cheems", "镜子里……我身后有人m！", "c40", emo={"cheems": "terror"}),
        P(2.4, "turn", sfx=[("whoosh", 0.0, 0.6), ("creak", 1.0, 0.7), ("click", 1.7, 0.8)]),
        L("cat", "趴下喵！", "k12", gap=0.2, sfx=[("hiss", 0.0, 0.6), ("crash", 0.35, 1.0)]),
        P(1.6, "dark"),
        L("cat", "看清楚了吗？那根本不是镜子，是窗户。", "k13", emo={"cat": "angry", "cheems": "shock"}),
        L("cat", "晚上屋里亮、屋外黑，窗户就会变成一面镜子。你看见的是你自己，可外面的人，把你看得清清楚楚。", "k14",
          emo={"cat": "normal"}),
        P(1.4, "retreat"),
    ], music="tension", amb="night_room"),

    # ------------------------------------------------------------ 04:20 真相
    Scene("truth", [
        L("cheems", "你……你到底是什么m？老金爷爷说，管理员不是猫m！", "c41", emo={"cheems": "scared"}),
        L("cat", "我当然是猫喵。不是猫，难道是面包吗？", "k15", emo={"cat": "lazy", "cheems": "confused"}),
        L("cat", "听好了。这里没有鬼，只有偷狗贼。", "k16", emo={"cat": "angry", "cheems": "shock"},
          sfx=[("sting", 0.0, 0.8)]),
        L("cat", "大门晚上有警报，他们进不来。可每扇门下面都有狗洞，狗能钻出去。所以，他们要想办法，让你们自己走出来。",
          "k17", emo={"cat": "normal", "cheems": "normal"}, sfx=[("card", 0.0, 0.7)]),
        L("cat", "第二只橘猫，是他们放进来的遥控玩具猫。它肚子里有一台夜视摄像头，靠狗狗眼睛的反光找目标。你闭上眼睛，它就看不见你。",
          "k18", sfx=[("card", 0.0, 0.7)]),
        L("cat", "肉骨头里下了药。吃下去，会睡得像块石头，被装进袋子都不知道。", "k19", sfx=[("card", 0.0, 0.7)]),
        L("cat", "还有那个，会学别人说话的——", "k20", gap=0.15),
        L("cheems", "是阿福！那只鹦鹉m！它在大堂听过我登记名字m！", "c42", emo={"cheems": "shock"},
          sfx=[("card", 0.0, 0.7)]),
        L("cat", "阿福是偷狗贼前几天寄养进来的。它能学小柯妈妈，能学哈士奇……可它不知道，那只傻哈士奇，一直管你叫芝士。",
          "k21", emo={"cheems": "normal"}),
        L("cheems", "所以……守则都是你写的m？", "c43", emo={"cheems": "sparkle"}),
        L("cat", "我是猫，打不过人，也管不住你们。我只能写守则。可是，总有不听话的狗。", "k22",
          emo={"cat": "sad", "cheems": "sad"}),
        L("cheems", "那老金爷爷给我的纸条……", "c44", emo={"cheems": "worried"}),
        P(1.2, "silent"),
        L("cat", "……天快亮了。他们还会再来一次。最后一次。", "k23", emo={"cat": "determined"}, gap=0.8),
    ], music="reveal", amb="night_room"),

    # ------------------------------------------------------------ 05:30 天亮
    Scene("dawn", [
        Card("05:30", "天亮了"),
        L("narr", "天蒙蒙亮。大堂的玻璃门外，站着一个穿蓝色卫衣的人。", "n9", emo={"cheems": "normal"}),
        L("owner_mimic", "Cheems，乖。我一定来接你。", "om1"),
        L("cheems", "主人m！", "c45", emo={"cheems": "joy"}, sfx=[("patter", 0.2, 0.7)]),
        P(1.6, "stop", emo={"cheems": "confused"}),
        L("cheems", "主人……你的红色牵引绳呢m？", "c46", emo={"cheems": "worried"}),
        L("owner_mimic", "Cheems，乖。我一定来接你。", "om2"),
        L("cheems", "它……只会说这一句m……", "c47", emo={"cheems": "scared"}, sfx=[("sting_soft", 0.0, 0.7)]),
        L("golden", "孩子，跟他走吧。", "j11", emo={"golden": "sad"}),
        L("cheems", "老金爷爷？", "c48", emo={"cheems": "shock"}),
        L("golden", "对不起……那张纸条，是那个人给我的。他说，只要我每天晚上，把一只狗骗到美容室，他就带我回家。", "j12",
          emo={"golden": "guilty", "cheems": "sad"}),
        L("golden", "我等我的主人，等了整整两年。他再也没有来过。我太想……有一个家了。", "j13",
          emo={"golden": "weep"}),
        L("cheems", "老金爷爷……他不会给你家的m。他只会把你也卖掉m。", "c49", emo={"cheems": "sad"}),
        P(1.0, "realize", emo={"golden": "cry"}),
        L("thief", "啰嗦什么！一只都别想跑！", "t1", sfx=[("glass", 0.0, 1.0)],
          emo={"cheems": "terror", "golden": "shock"}),
    ], music="tension2", amb="dawn"),

    # ------------------------------------------------------------ 反击
    Scene("fight", [
        L("cat", "Cheems！叫醒所有的狗喵！", "k24", emo={"cat": "angry", "cheems": "shock"}),
        L("cheems", "二哈！快醒醒m！用你这辈子最大的声音！", "c50", emo={"cheems": "determined"},
          sfx=[("patter", 0.0, 0.7)]),
        L("husky", "嗯？芝士？你终于主动找我玩啦？", "h6", emo={"husky": "sleepy"}),
        L("cheems", "别废话m！嚎m！", "c51", emo={"cheems": "angry"}),
        L("husky", "嗷呜——————！", "h7", emo={"husky": "joy"}, gap=0.6, fx="howl", speed=0.6,
          sfx=[("howl_boom", 0.0, 1.0)]),
        P(2.4, "chorus", sfx=[("bark_chorus", 0.0, 0.9)]),
        L("thief", "该死！这哈士奇是警报器吗！", "t2", emo={"cheems": "determined"}),
        P(0.5, "lunge", sfx=[("whoosh", 0.0, 0.7)]),
        L("golden", "不许碰这孩子！", "j14", emo={"golden": "angry"}, sfx=[("thud", 0.6, 0.9)]),
        L("cat", "喵——！", "k25", emo={"cat": "angry"}, sfx=[("scratch_fast", 0.0, 0.9)]),
        L("cheems", "坏人m！吃我一口m！", "c52", emo={"cheems": "angry"}, sfx=[("tear", 0.8, 0.8)]),
        P(2.2, "slip", sfx=[("squeak", 0.3, 0.9), ("slip", 0.5, 0.8), ("crash", 1.1, 1.0)]),
    ], music="action", amb="dawn"),

    Scene("van", [
        L("zhuang", "嗯？谁打扰我睡觉……这是哪儿？", "z6", emo={"zhuang": "sleepy", "corgi": "cry"}),
        L("corgi", "大壮哥哥！我们被关起来了！", "g6", emo={"corgi": "cry", "zhuang": "shock"}),
        L("zhuang", "关我？你知道我每天做多少个俯卧撑吗！", "z7", emo={"zhuang": "angry"}),
        L("zhuang", "蛋白质——之力！", "z8", emo={"zhuang": "angry"}, sfx=[("metal_bend", 0.4, 1.0)]),
        P(1.2, "burst", sfx=[("boom", 0.0, 0.8)], emo={"zhuang": "proud", "corgi": "sparkle"}),
        L("parrot", "完蛋了！完蛋了！完蛋了！", "p3", sfx=[("wings", 0.0, 0.6)]),
        L("narr", "邻居们被二哈的嚎叫吵醒，报了警。偷狗贼和他的鹦鹉，一起被带上了警车。", "n10",
          sfx=[("siren", 0.0, 0.8)]),
    ], music="action", amb="dawn"),

    # ------------------------------------------------------------ 早晨：大橘
    Scene("morning", [
        L("staff", "天哪！我就回家睡了一晚，怎么出了这么大的事！你们都没事吧？", "s1", sfx=[("door_bell", 0.0, 0.6)],
          emo={"cheems": "normal"}),
        L("corgi", "Cheems哥哥，谢谢你！", "g7", emo={"corgi": "joy", "cheems": "happy"}),
        L("zhuang", "兄弟，以后你就是我大哥！我发誓，再也不乱吃东西了。", "z9", emo={"zhuang": "happy"}),
        L("cheems", "要谢就谢管理员姐姐m。守则都是她写的m。", "c53", emo={"cheems": "proud"}),
        L("staff", "守则？什么守则？我们店里……从来没写过什么夜间守则啊。", "s2", emo={"cheems": "confused"}),
        L("cheems", "就是那只橘猫m，夜班管理员m！", "c54", emo={"cheems": "normal"}),
        P(1.4, "freeze"),
        L("staff", "橘猫……你说的，是大橘吗？", "s3", emo={"cheems": "worried"}),
        P(2.6, "plaque", sfx=[("sting_soft", 0.2, 0.6)]),
        L("staff", "大橘是我们店以前的店猫。七年前的一个夜里，它为了保护店里的狗狗……就再也没有回来。", "s4",
          emo={"cheems": "sad"}),
        P(2.8, "turn"),
        L("cat", "这一次，一只都没有少喵。", "k26", fx="ethereal", emo={"cheems": "weep", "cat": "happy"}),
        P(3.0, "fade", sfx=[("shimmer", 0.0, 0.8)]),
        L("cheems", "原来……管理员，真的不是猫m……", "c55", emo={"cheems": "weep"}, gap=1.0),
    ], music="warm", amb="morning"),

    # ------------------------------------------------------------ 主人来了
    Scene("reunion", [
        L("owner", "Cheems！店里打电话说出事了，我连夜坐车赶回来的！你没事吧！", "o3",
          sfx=[("door_bell", 0.0, 0.6), ("run", 0.0, 0.6)], emo={"cheems": "shock"}),
        L("cheems", "红色牵引绳m……是真的主人m！", "c56", emo={"cheems": "joy"}),
        P(2.4, "hug", sfx=[("sparkle", 0.3, 0.6)], emo={"cheems": "happy"}),
        L("cheems", "主人，我们能不能……把老金爷爷也带回家m？", "c57", emo={"cheems": "worried"}),
        L("owner", "听说，是您扑倒了坏人，保护了我们家Cheems？", "o4", emo={"golden": "guilty"}),
        L("golden", "我……", "j15", gap=0.4),
        L("cheems", "嗯m！老金爷爷可勇敢了m！", "c58", emo={"cheems": "happy"}),
        L("owner", "那……老先生，愿意跟我们回家吗？", "o5"),
        L("golden", "家……我也……可以有家吗？", "j16", emo={"golden": "weep"}),
        P(2.6, "wag", emo={"golden": "happy"}),
    ], music="warm", amb="morning"),

    # ------------------------------------------------------------ 尾声
    Scene("epilogue", [
        L("narr", "后来，月光宠物旅馆换上了更结实的门窗。大堂里，大橘的照片前，每天都会多出一小碗猫粮。", "n11"),
        L("narr", "而Cheems的新家里，也贴上了一份新的守则。", "n12"),
        L("owner", "家规第一条：晚上十点以后，不准偷吃零食。", "o6"),
        L("cheems", "第二条：家规里有一条是假的m。", "c59", emo={"cheems": "smug"}, sfx=[("crayon", 0.0, 0.7)]),
        L("owner", "Cheems！", "o7", emo={"cheems": "shock"}),
        L("cheems", "嘿嘿m。", "c60", emo={"cheems": "smug"}, gap=1.0),
        P(3.4, "window", sfx=[("shimmer", 1.0, 0.6)]),
        L("rules", "第七条：本守则，全部为真。", "r7c", gap=1.2),
        P(9.0, "credits"),
    ], music="ending", amb="night_room"),
]


def all_lines():
    for sc in SCENES:
        for b in sc.beats:
            if b.kind == "line":
                yield sc, b


if __name__ == "__main__":
    n = sum(len(b.text) for _, b in all_lines())
    print("台词数", sum(1 for _ in all_lines()), "总字数", n)
