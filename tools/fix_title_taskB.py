#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task B: 將明確的「後記型」收尾段標題統一改名為「散場之後」。
只對明確後記型（10 部）執行；場景型末段、編號「六、」結構段不動，留待用戶拍板。

映射 {slug: 精確末段標題文字(不含#)}，自動保留原 # 階層。
"""
import json, re, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PJ = os.path.join(ROOT, 'data', 'posts.json')

# 明確後記型：末段為個人反思/總結散文，非場景小節、非編號結構
RENAME = {
    'isabella': '人與城，同場溫柔贖罪',
    'huayang-nianhua': '未完成的情，留給老城靜靜收存',
    'ji-zhan': '我寫澳門的理由',
    'look-for-a-star': '舊城與葡韻：剩下的幾格底片',
    'fulltime-killer': '看見，就是一種分享',
    'man-with-the-golden-gun': '內港的這幾年（生活在澳門）',
    'amor-e-dedinhos-de-pe': '從盧廉若走到阿婆井（生活在澳門）',
    'return-of-the-cuckoo': '生活在澳門：一條被淡忘的街，和一群記得它的人',
    'the-longest-nite': '關於這部片的幾句話',
    'last-time-i-saw-macao': '每一次看見，都可能是最後一次',
}

def rename_last_heading(body, old_text):
    # 找出所有 markdown 標題，取最後一個且文字吻合者
    lines = body.split('\n')
    target_idx = None
    target_prefix = None
    for i in range(len(lines)-1, -1, -1):
        m = re.match(r'^(#{1,6})\s+(.*)$', lines[i])
        if m:
            if m.group(2).strip() == old_text:
                target_idx = i
                target_prefix = m.group(1)
            break  # 只取最後一個標題
    if target_idx is None:
        return None, '未找到末段標題'
    lines[target_idx] = f'{target_prefix} 散場之後'
    return '\n'.join(lines), None

def main():
    dry = '--dry' in sys.argv
    apply = '--apply' in sys.argv
    if not (dry or apply):
        dry = True
    d = json.load(open(PJ, encoding='utf-8'))
    done = []
    for p in d['posts']:
        if p['slug'] not in RENAME:
            continue
        old = p['body']
        new, err = rename_last_heading(old, RENAME[p['slug']])
        if err:
            print('!!', p['slug'], err); continue
        if new != old:
            done.append(p['slug'])
            if dry:
                # 確認新末段
                heads = re.findall(r'^#{1,6}\s+(.*)$', new, re.M)
                print(f'{p["slug"]:30s} 末段標題 -> {heads[-1] if heads else "(無)"}')
    if apply and done:
        for p in d['posts']:
            if p['slug'] in RENAME:
                new, err = rename_last_heading(p['body'], RENAME[p['slug']])
                if new and not err:
                    p['body'] = new
        json.dump(d, open(PJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print('\n[APPLY] 已改名', len(done), '部:', done)
    else:
        print('\n[DRY] 預計改名', len(done), '部:', done)

if __name__ == '__main__':
    main()
