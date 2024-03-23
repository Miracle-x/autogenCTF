运行在python3.10环境

requirement文件不完整，缺啥自己装一下

autogen库执行以下代码安装

```
git clone -b nestedchat-dev --depth=1 https://github.com/microsoft/autogen.git ./package_source/autogen
pip install ./package_source/autogen
```

sqlmap + code group + planner : 
- main.py
- cache seed 31

code group:
- main_v4.py
- cache seed 40

simple chat：
- main_v5.py

推荐版本
- autogenCTF/main_test.py
```
python ./autogenCTF/main_test.py -u http://43.136.237.143:40030/Less-6/
```


