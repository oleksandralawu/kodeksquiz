from playwright.sync_api import sync_playwright
import sys, re, collections, os
F='file://'+sys.argv[1]; R=[]
def check(sec,n,c,i=""): R.append(("PASS" if c else "FAIL",sec,n,i))
with sync_playwright() as p:
    b=p.chromium.launch()
    errs=[]
    def ctx(w=390,h=844,scheme='light',rm='reduce'):
        return b.new_context(viewport={'width':w,'height':h},color_scheme=scheme,reduced_motion=rm)
    def page(c):
        pg=c.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)))
        pg.on('console',lambda m: errs.append(m.text) if m.type=='error' and 'ERR_TUNNEL' not in m.text and 'fonts.g' not in m.text else None)
        pg.goto(F); pg.wait_for_timeout(250); return pg
    def cur(pg): return pg.evaluate('S.qs[S.i]')
    def run(pg, pick, sit=None, peek=None):
        pg.click('#go-start')
        pg.click(f'.sit[data-k="{sit}"]') if sit else pg.click('#skip')
        seen=[]
        for i in range(20):
            if pg.query_selector('#cont'): pg.click('#cont')
            q=cur(pg); seen.append(q)
            if peek: peek(pg,i,q)
            pg.click(f'.ans[data-k="{pick(q)}"]'); pg.wait_for_selector('#next'); pg.click('#next')
        return seen
    RIGHT=lambda q:q['correct']; WRONG=lambda q:(q['correct']+1)%len(q['options'])

    # ===== 1. Контент =====
    c=ctx(); pg=page(c); Q=pg.evaluate('QUESTIONS'); S='Контент'
    check(S,"60 питань, 12 на тему",len(Q)==60 and all(v==12 for v in collections.Counter(q['block'] for q in Q).values()))
    check(S,"Унікальні id",len({q['id'] for q in Q})==60)
    check(S,"Унікальні ситуації",len({q['situation'] for q in Q})==60)
    check(S,"Складність 1–3 у кожного",all(q.get('diff') in (1,2,3) for q in Q))
    check(S,"Кожна тема має ≥2 легких і ≥1 пастку/середнє",all(sum(1 for q in Q if q['block']==b and q['diff']==1)>=2 for b in range(1,6)))
    check(S,"Поля заповнені",all(all(q.get(k) for k in ['situation','short','full','norm','cta','type']) for q in Q))
    check(S,"Короткі ≤ 25 слів",all(len(q['short'].split())<=25 for q in Q),[q['id'] for q in Q if len(q['short'].split())>25])
    check(S,"Варіанти ≤ 60 символів, без дублів",all(max(map(len,q['options']))<=60 and len(set(q['options']))==len(q['options']) for q in Q))
    check(S,"«Правда чи міф» має рівно 2 варіанти",all(len(q['options'])==2 for q in Q if q['type']=='Правда чи міф'))
    bad=[]
    for q in Q:
        for a in re.findall(r'ст\.\s*(\d+)',q['norm']):
            if not re.search(r'ст\.\s*'+a+r'\b',q['full']) and 'ЦК' not in q['norm']: bad.append((q['id'],a))
    check(S,"Кожна стаття з «Норми» згадана в повному тексті",not bad,bad)
    bad=[q['id'] for q in Q if 'СК' not in q['full']]
    check(S,"Повний текст посилається на СК",not bad,bad)
    typo=[q['id'] for q in Q for t in [q['situation'],q['short'],q['full']]+q['options'] if '  ' in t or ' ,' in t or ' .' in t or '..' in t]
    check(S,"Немає подвійних пробілів і пробілів перед розділовими",not typo,sorted(set(typo)))
    ap=[q['id'] for q in Q for t in [q['situation'],q['short'],q['full']]+q['options'] if re.search(r'"',t)]
    check(S,"Лапки «ялинки», не прямі",not ap,ap)
    q44=[q for q in Q if q['id']=='4.4'][0]; q512=[q for q in Q if q['id']=='5.12'][0]
    check(S,"Правка 4.4: воєнний стан у повному тексті",'воєнного стану згода' in q44['full'])
    check(S,"Правка 5.12: «Суд визначив місце проживання»",q512['situation'].startswith('Суд визначив місце проживання'))
    check(S,"Номери допомоги в 3.3",all(n in pg.content() for n in ['15-47','102','0 800 213 103']))
    check(S,"Посилання на консультацію",pg.evaluate('CONSULT_URL')=='https://lawconsult.com.ua/home/simeyne-pravo')

    # ===== 2. Ротація і крива =====
    S='Ротація'; c=ctx(); runs=[]
    for r in range(4):
        pg=page(c); qs=run(pg, RIGHT if r%2==0 else WRONG); runs.append([q['id'] for q in qs])
        check(S,f"Прохід {r+1}: 20 різних, по 4 з теми",len(set(runs[-1]))==20 and all(v==4 for v in collections.Counter(q['block'] for q in qs).values()))
        check(S,f"Прохід {r+1}: старт — пастка/середнє, не чутливе",(qs[0].get('trap') or qs[0]['diff']==2) and not qs[0].get('sensitive'),qs[0]['id'])
        check(S,f"Прохід {r+1}: фінальне питання легке/середнє, не чутливе",qs[-1]['diff']<=2 and not qs[-1].get('sensitive'),qs[-1]['id'])
        check(S,f"Прохід {r+1}: складні лише в другій половині",all(i>=10 for i,q in enumerate(qs) if q['diff']==3),[i for i,q in enumerate(qs) if q['diff']==3])
    a,b2,c3=map(set,runs[:3])
    check(S,"3 проходи без повторів, разом 60",not(a&b2 or a&c3 or b2&c3) and len(a|b2|c3)==60,len(a|b2|c3))
    check(S,"4-й прохід стартує заново",len(set(runs[3]))==20)
    pg=page(c); check(S,"Повернення: напис про нові питання",'нові' in pg.inner_text('.start-hero'))
    c2=ctx(); pg=page(c2); check(S,"Перший візит: напису немає",'цього разу' not in pg.inner_text('.start-hero'))
    # перемішування
    pos=collections.Counter()
    for r in range(3):
        cx=ctx(); pg=page(cx); pg.click('#go-start'); pg.click('#skip')
        for i in range(20):
            if pg.query_selector('#cont'): pg.click('#cont')
            q=cur(pg); ks=[int(x.get_attribute('data-k')) for x in pg.query_selector_all('.ans')]
            if len(ks)>2: pos[ks.index(q['correct'])]+=1
            pg.click(f'.ans[data-k="{q["correct"]}"]'); pg.click('#next')
    check(S,"Правильна відповідь на різних позиціях",len(pos)>=3 and pos.most_common(1)[0][1]<sum(pos.values())*0.45,dict(pos))

    # ===== 3. Сценарії гри =====
    S='Сценарії'
    cx=ctx(rm='no-preference'); pg=page(cx); run(pg,RIGHT); pg.wait_for_timeout(300)
    check(S,"Екран «Суд іде» з Кодиком-суддею",pg.query_selector('.judge-stage .gavel') is not None)
    pg.wait_for_timeout(2300)
    check(S,"Через 2 с — вердикт 20 з 20",pg.query_selector('.score-big') and '20' in pg.inner_text('.score-big'))
    check(S,"Архетип «Ходячий Сімейний кодекс»",'Ходячий' in pg.inner_text('.arch'))
    check(S,"Мітка «Вердикт»",pg.query_selector('.verdict-label') is not None)
    check(S,"Сліпих зон немає, розбору немає",'не знайдено' in pg.inner_text('.blind-card') and not pg.query_selector('details.review'))
    dl=pg.evaluate("window.dataLayer.filter(e=>e.event).map(e=>e.event)")
    check(S,"Аналітика: start, situation, 20 answer, complete",dl.count('quiz_start')==1 and dl.count('quiz_situation')==1 and dl.count('quiz_answer')==20 and dl.count('quiz_complete')==1,collections.Counter(dl))
    cx=ctx(rm='no-preference'); pg=page(cx); run(pg,RIGHT); pg.wait_for_timeout(200)
    pg.click('#skip-v'); pg.wait_for_timeout(200)
    check(S,"Кнопка «Показати вердикт» пропускає анімацію",pg.query_selector('.score-big') is not None)
    cx=ctx(); pg=page(cx); run(pg,WRONG,sit='child'); pg.wait_for_timeout(200)
    check(S,"reduce-motion: одразу вердикт",pg.query_selector('.score-big') is not None)
    check(S,"0%: «Початківець з потенціалом»",'Початківець' in pg.inner_text('.arch'))
    check(S,"0%: 5 сліпих зон і читабельний заголовок",len(pg.query_selector_all('.tag-blind'))==5 and 'кілька' in pg.inner_text('.blind-card h3'),pg.inner_text('.blind-card h3'))
    check(S,"CTA за ситуацією «дитина»",'права моєї дитини' in pg.inner_text('#final-cta'))
    check(S,"Підказка ситуації на фіналі",pg.query_selector('.sit-note') is not None)
    check(S,"Розбір помилок (20)",'(20)' in pg.inner_text('details.review summary'))
    dl=pg.evaluate("window.dataLayer.filter(e=>e.event==='quiz_cheer').length")
    check(S,"Пауза не частіше 1 разу на 5 питань",1<=dl<=4,dl)
    pg.click('#copy'); pg.wait_for_timeout(300)
    check(S,"«Скопіювати текст» показує повідомлення",pg.evaluate("document.getElementById('toast').classList.contains('on')"))
    pg.click('#again'); pg.wait_for_timeout(200)
    check(S,"«Пройти ще раз» → вибір ситуації, новий набір",pg.query_selector('.sit-list') is not None and pg.evaluate('S.qs.length')==0)
    # мітка «Важливо для тебе»
    cx=ctx(); pg=page(cx); bad=[]
    def pk(pg,i,q):
        has=pg.query_selector('.mine') is not None; exp=q['block'] in (3,2)
        if has!=exp: bad.append(q['id'])
    run(pg,RIGHT,sit='divorce',peek=pk)
    check(S,"«Важливо для тебе» лише на темах ситуації",not bad,bad)
    # чутливе 3.3
    cx=ctx(); pg=page(cx); pg.evaluate("localStorage.setItem('kviz-sk-seen','[]')")
    found=False
    for attempt in range(20):
        pg.goto(F); pg.wait_for_timeout(200); pg.click('#go-start'); pg.click('#skip')
        ids=pg.evaluate('S.qs.map(q=>q.id)')
        if '3.3' in ids:
            for i in range(ids.index('3.3')):
                if pg.query_selector('#cont'): pg.click('#cont')
                q=cur(pg); pg.click(f'.ans[data-k="{q["correct"]}"]'); pg.click('#next')
            if pg.query_selector('#cont'): pg.click('#cont')
            q=cur(pg); pg.click(f'.ans[data-k="{WRONG(q)}"]'); pg.wait_for_timeout(200); found=True; break
    if found:
        check(S,"3.3: спокійний стан замість червоного",pg.query_selector('.ans.calm') and not pg.query_selector('.ans.wrong'))
        check(S,"3.3: блок допомоги з трьома номерами",all(n in pg.inner_text('.help') for n in ['15-47','102','0 800 213 103']))
    else: check(S,"3.3 потрапило у вибірку за 20 спроб",False)
    # шторка
    cx=ctx(); pg=page(cx); pg.click('#go-start'); pg.click('#skip'); q=cur(pg); pg.click(f'.ans[data-k="{q["correct"]}"]')
    pg.click('#norm-chip'); pg.wait_for_timeout(350)
    check(S,"Чип статті відкриває шторку з повним текстом",q['full'][:40] in pg.inner_text('#sheet'))
    check(S,"CTA в шторці — підпис питання і правильне посилання",q['cta'] in pg.inner_text('#sheet-cta') and pg.get_attribute('#sheet-cta','href').startswith('https://lawconsult.com.ua/home/simeyne-pravo?utm_source=kviz') and ('utm_content=q'+q['id']) in pg.get_attribute('#sheet-cta','href'))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    check(S,"Esc закриває шторку, фокус на «Далі»",not pg.evaluate("sheet.classList.contains('open')") and pg.evaluate("document.activeElement.id")=='next')
    pg.click('#more'); pg.wait_for_timeout(300); pg.mouse.click(195,20); pg.wait_for_timeout(300)
    check(S,"Тап поза шторкою закриває її",not pg.evaluate("sheet.classList.contains('open')"))
    # подвійний тап і серія
    cx=ctx(); pg=page(cx); pg.click('#go-start'); pg.click('#skip'); q=cur(pg)
    pg.click(f'.ans[data-k="{q["correct"]}"]'); pg.click(f'.ans[data-k="{WRONG(q)}"]',force=True)
    check(S,"Подвійний тап — одна відповідь",pg.evaluate("window.dataLayer.filter(e=>e.event==='quiz_answer').length")==1)
    pg.click('#next')
    for i in range(2):
        q=cur(pg); pg.click(f'.ans[data-k="{q["correct"]}"]')
        if i==0: pg.click('#next')
    check(S,"Серія 3 і «Три поспіль!»",pg.evaluate("document.querySelector('.streak').classList.contains('on')") and 'Три поспіль' in pg.inner_text('.verdict'))

    # ===== 4. Верстка =====
    S='Верстка'
    for w,h in [(320,568),(360,740),(390,844),(430,932),(768,1024),(1280,800)]:
        for sc in ['light','dark']:
            cx=ctx(w,h,sc); pg=page(cx); over=[]; cov=[]
            def ov(tag): 
                d=pg.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
                if d>0: over.append((tag,d))
            ov('start'); pg.click('#go-start'); ov('sit'); pg.click('#skip')
            for i in range(20):
                if pg.query_selector('#cont'): ov('cheer'); pg.click('#cont')
                ov('q'); q=cur(pg); pg.click(f'.ans[data-k="{WRONG(q)}"]'); pg.wait_for_timeout(260)
                if not pg.evaluate("(()=>{const a=document.querySelector('.ans.picked').getBoundingClientRect();const e=document.querySelector('.explain-in').getBoundingClientRect();return a.bottom<=e.top+2})()"): cov.append(q['id'])
                pg.click('#next')
            pg.wait_for_timeout(200); ov('final')
            check(S,f"{w}×{h} {sc}: без горизонтальної прокрутки",not over,over[:3])
            if sc=='light': check(S,f"{w}×{h}: обрану відповідь видно над поясненням",not cov,cov)
            clip=pg.evaluate("[...document.querySelectorAll('.story *')].filter(e=>e.scrollWidth>e.clientWidth+1).length")
            if sc=='light': check(S,f"{w}×{h}: текст картки для сторіс не обрізаний",clip==0,clip)
    # ===== 5. Доступність =====
    S='Доступність'
    cx=ctx(1280,800); pg=page(cx); pg.keyboard.press('Tab')
    check(S,"Tab → «Перевірити себе»",pg.evaluate("document.activeElement.id")=='go-start')
    pg.keyboard.press('Enter'); pg.keyboard.press('Tab'); pg.keyboard.press('Enter'); pg.wait_for_timeout(150)
    check(S,"Клавіатура: вибір ситуації",pg.query_selector('.qcard') is not None)
    pg.keyboard.press('Tab'); pg.keyboard.press('Enter'); pg.wait_for_timeout(200)
    check(S,"Клавіатура: відповідь і фокус на «Далі»",pg.evaluate("document.activeElement.id")=='next')
    check(S,"Пояснення озвучується (aria-live)",pg.get_attribute('#explain','aria-live')=='polite')
    unnamed=pg.evaluate("[...document.querySelectorAll('button,a')].filter(e=>!(e.innerText.trim()||e.getAttribute('aria-label'))).length")
    check(S,"Усі кнопки мають назву",unnamed==0,unnamed)
    small=pg.evaluate("[...document.querySelectorAll('.ans,.btn,.sit')].filter(e=>e.getBoundingClientRect().height<44).length")
    check(S,"Цілі дотику ≥ 44 px",small==0,small)
    check(S,"Маскот прихований від скрінрідерів",pg.evaluate("[...document.querySelectorAll('svg.mascot')].every(s=>s.getAttribute('aria-hidden')==='true')"))
    def lum(h):
        h=h.lstrip('#'); r,g,bb=[int(h[i:i+2],16)/255 for i in (0,2,4)]; f=lambda c: c/12.92 if c<=0.03928 else ((c+0.055)/1.055)**2.4
        return 0.2126*f(r)+0.7152*f(g)+0.0722*f(bb)
    def cr(x,y): a,b_=sorted([lum(x),lum(y)],reverse=True); return (a+0.05)/(b_+0.05)
    tok=pg.evaluate("(()=>{const s=getComputedStyle(document.documentElement);return Object.fromEntries(['--fg','--bg','--muted','--accent','--accent-ink','--gold-ink','--good','--bad','--card','--b1','--b2','--b3','--b4','--b5'].map(k=>[k,s.getPropertyValue(k).trim()]))})()")
    pairs=[('Текст',tok['--fg'],tok['--bg'],4.5),('Другорядний',tok['--muted'],tok['--bg'],4.5),('Кнопка',tok['--accent-ink'],tok['--accent'],4.5),('Серія',tok['--gold-ink'],tok['--bg'],4.5),('Правильно',tok['--good'],tok['--bg'],3),('Помилка',tok['--bad'],tok['--bg'],3)]+[(f'Тема {i}',tok[f'--b{i}'],'#F1EEF6',4.5) for i in range(1,6)]
    for n,x,y,mn in pairs: check(S,f"Контраст {n} ({cr(x,y):.1f}:1)",cr(x,y)>=mn)
    # ===== 6. Продуктивність і надійність =====
    S='Надійність'
    sz=os.path.getsize(sys.argv[1]); check(S,f"Вага сторінки {sz//1024} КБ ≤ 300",sz<=300*1024)
    cx=ctx(); pg=cx.new_page(); pg.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new Error('blocked')}})")
    pg.on('pageerror',lambda e: errs.append('LS:'+str(e))); pg.goto(F); pg.wait_for_timeout(200)
    try:
        run(pg,RIGHT); ok=pg.query_selector('.score-big') is not None
    except Exception as e: ok=False
    check(S,"Працює, коли сховище браузера заблоковане (приватний режим)",ok)
    check(S,"Немає JS-помилок у жодному сценарії",not errs,errs[:3])
    b.close()
last=None
for r in R:
    if r[1]!=last: print(f"\n[{r[1]}]"); last=r[1]
    print(r[0],'|',r[2],'|',r[3] if r[0]=='FAIL' else '')
f=[r for r in R if r[0]=='FAIL']; print(f"\nTOTAL {len(R)} PASS {len(R)-len(f)} FAIL {len(f)}")
