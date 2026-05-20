import flet as ft
from geopy.distance import geodesic
import winsound
import threading
import time
import pyttsx3
import flet_geolocator as gl

engine = pyttsx3.init()
engine.setProperty('rate', 190)
engine.setProperty('volume', 0.9)

def falar(mensagem, callback=None):
    """Fala uma mensagem e, se callback for fornecido, executa após o fim da fala"""
    def _falar():
        engine.say(mensagem)
        engine.runAndWait()
        if callback:
            callback()
    threading.Thread(target=_falar, daemon=True).start()

# ------------------- TELA DO JOGO -------------------
def tela_jogo(page: ft.Page, pistas):
    page.clean()
    page.title = "Caça ao Tesouro"
    page.padding = 20
    page.window_width = 500
    page.window_height = 700
    page.bgcolor = "#F0F4F8"

    pista_atual = 0
    loop_ativo = False
    thread_bip = None

    def tocar_bip_continuo(distancia):
        nonlocal loop_ativo
        if distancia < 3:
            intervalo = 0.07
            frequencia = 3000
        elif distancia < 8:
            intervalo = 0.15
            frequencia = 2500
        elif distancia < 15:
            intervalo = 0.3
            frequencia = 2000
        elif distancia < 30:
            intervalo = 0.6
            frequencia = 1500
        elif distancia < 50:
            intervalo = 1.0
            frequencia = 1000
        else:
            intervalo = 1.5
            frequencia = 600
        while loop_ativo:
            winsound.Beep(frequencia, 100)
            time.sleep(intervalo)

    def parar_bip():
        nonlocal loop_ativo, thread_bip
        loop_ativo = False
        if thread_bip and thread_bip.is_alive():
            thread_bip.join(timeout=0.5)

    def iniciar_bip(distancia):
        nonlocal loop_ativo, thread_bip
        parar_bip()
        loop_ativo = True
        thread_bip = threading.Thread(target=tocar_bip_continuo, args=(distancia,), daemon=True)
        thread_bip.start()

    def tocar_acerto():
        winsound.Beep(1000, 100)
        winsound.Beep(1500, 100)
        winsound.Beep(2000, 100)

    icone = ft.Text(pistas[pista_atual]["icone"], size=80)
    nome = ft.Text(f"Pista {pista_atual+1}", size=24, weight="bold", color="#1a1a2e")
    header = ft.Row([icone, nome], alignment="center", spacing=20)

    distancia_texto = ft.Text("--- m", size=18, color="#1a1a2e", weight="bold")
    barra = ft.ProgressBar(value=0, width=300, height=20, color="blue")
    termometro = ft.Column([distancia_texto, barra], horizontal_alignment="center", spacing=10)

    bip_status = ft.Text("🔊 Aguardando localização...", size=12, color="#555")

    lat_input = ft.TextField(label="Latitude", value=str(pistas[pista_atual]["lat"]), width=180)
    lon_input = ft.TextField(label="Longitude", value=str(pistas[pista_atual]["lon"]), width=180)
    linha_gps = ft.Row([lat_input, lon_input], alignment="center", spacing=20)

    btn_atualizar = ft.Button("📍 Atualizar", on_click=lambda e: atualizar())
    btn_achei = ft.Button("✅ ACHEI", disabled=True, on_click=lambda e: proxima())
    
    def voltar_config(e):
        parar_bip()
        tela_configuracao(page)
    btn_reconfig = ft.Button("⚙️ Reconfigurar Pistas", on_click=voltar_config)
    
    linha_botoes = ft.Row([btn_atualizar, btn_achei], alignment="center", spacing=30)

    layout = ft.Column(
        [
            header,
            ft.Divider(height=30, color="transparent"),
            termometro,
            bip_status,
            ft.Divider(height=40, color="transparent"),
            ft.Text("📱 Simular GPS (teste)", size=16, weight="bold", color="#1a1a2e"),
            linha_gps,
            ft.Divider(height=30, color="transparent"),
            linha_botoes,
            ft.Divider(height=20, color="transparent"),
            btn_reconfig,
        ],
        horizontal_alignment="center",
        spacing=20,
    )
    page.add(layout)

    def calcular_distancia(lat1, lon1, lat2, lon2):
        return geodesic((lat1, lon1), (lat2, lon2)).meters

    def atualizar():
        nonlocal pista_atual
        if pista_atual >= len(pistas):
            parar_bip()
            distancia_texto.value = "🏆 FIM!"
            barra.value = 1
            barra.color = "green"
            btn_achei.disabled = True
            bip_status.value = "🔊 Jogo finalizado"
            page.update()
            return
        try:
            lat = float(lat_input.value)
            lon = float(lon_input.value)
        except:
            distancia_texto.value = "Erro"
            page.update()
            return

        alvo = pistas[pista_atual]
        dist = calcular_distancia(lat, lon, alvo["lat"], alvo["lon"])
        quente = max(0, min(1, 1 - dist / 50))
        barra.value = quente
        distancia_texto.value = f"{dist:.1f} m"

        iniciar_bip(dist)

        if dist < 3:
            bip_status.value = "🔊 Bip: MUITO RÁPIDO + AGUDO"
        elif dist < 8:
            bip_status.value = "🔊 Bip: muito rápido + agudo"
        elif dist < 15:
            bip_status.value = "🔊 Bip: rápido + médio"
        elif dist < 30:
            bip_status.value = "🔊 Bip: médio"
        elif dist < 50:
            bip_status.value = "🔊 Bip: lento + grave"
        else:
            bip_status.value = "🔊 Bip: muito lento + grave"

        if quente > 0.8:
            barra.color = "red"
            distancia_texto.value = f"🌋 {dist:.1f} m"
            btn_achei.disabled = False
        elif quente > 0.5:
            barra.color = "orange"
            btn_achei.disabled = True
        elif quente > 0.2:
            barra.color = "yellow"
            btn_achei.disabled = True
        else:
            barra.color = "blue"
            btn_achei.disabled = True
        page.update()

    def proxima():
        nonlocal pista_atual
        if pista_atual < len(pistas):
            pista_atual += 1
            btn_achei.disabled = True
            parar_bip()
            if pista_atual < len(pistas):
                icone.value = pistas[pista_atual]["icone"]
                nome.value = f"Pista {pista_atual+1}"
                lat_input.value = str(pistas[pista_atual]["lat"])
                lon_input.value = str(pistas[pista_atual]["lon"])
                page.update()
            else:
                page.update()
                return
            threading.Thread(target=tocar_acerto, daemon=True).start()
            atualizar()

    # Inicialização: calcula distância inicial mas não inicia o bip ainda
    lat0 = float(lat_input.value)
    lon0 = float(lon_input.value)
    dist_inicial = calcular_distancia(lat0, lon0, pistas[0]["lat"], pistas[0]["lon"])
    quente = max(0, min(1, 1 - dist_inicial / 50))
    barra.value = quente
    distancia_texto.value = f"{dist_inicial:.1f} m"
    if quente > 0.8:
        barra.color = "red"
        distancia_texto.value = f"🌋 {dist_inicial:.1f} m"
        btn_achei.disabled = False
    elif quente > 0.5:
        barra.color = "orange"
        btn_achei.disabled = True
    elif quente > 0.2:
        barra.color = "yellow"
        btn_achei.disabled = True
    else:
        barra.color = "blue"
        btn_achei.disabled = True
    bip_status.value = "🔊 Bip iniciará após a mensagem de boas-vindas..."
    page.update()

    # Não inicia o bip agora – ele será iniciado pela função callback da fala
    # Precisamos armazenar a distância inicial para quando o bip começar
    def iniciar_bip_apos_voz():
        iniciar_bip(dist_inicial)
        bip_status.value = "🔊 Bip ativo! Aproxime-se do tesouro."
        page.update()
    
    # Retornamos a função para ser usada como callback lá fora
    return iniciar_bip_apos_voz

# ------------------- TELA DE CONFIGURAÇÃO -------------------
def tela_configuracao(page: ft.Page, pistas_existentes=None):
    page.clean()
    page.title = "Configurar Pistas"
    page.padding = 20
    page.window_width = 700
    page.window_height = 800
    page.bgcolor = "#F0F4F8"

    if pistas_existentes is None:
        pistas_existentes = [
            {"icone": "🏊", "lat": -23.5505, "lon": -46.6333},
            {"icone": "🍿", "lat": -23.5500, "lon": -46.6340},
            {"icone": "🔥", "lat": -23.5510, "lon": -46.6325},
            {"icone": "🎈", "lat": -23.5495, "lon": -46.6345},
            {"icone": "⭐", "lat": -23.5508, "lon": -46.6338},
        ]

    campos = []
    geolocator = gl.Geolocator()
    # page.overlay.append(geolocator)  # comentado para evitar barra vermelha

    titulo = ft.Text("🏆 Caça ao Tesouro do Theo 🏆", size=28, weight="bold", color="#1a1a2e")
    subtitulo = ft.Text("Digite as coordenadas ou use o botão 📍 para capturar a localização atual:", size=16, color="#555")

    grupos = ft.Column(spacing=25)
    for i, p in enumerate(pistas_existentes):
        num_pista = ft.Text(f"Pista {i+1} - {p['icone']}", size=18, weight="bold")
        lat_field = ft.TextField(label=f"Latitude Pista {i+1}", value=str(p["lat"]), width=200)
        lon_field = ft.TextField(label=f"Longitude Pista {i+1}", value=str(p["lon"]), width=200)
        
        def fazer_captura(idx, lat_f, lon_f):
            def capturar(e):
                pos = geolocator.get_current_position()
                if pos:
                    lat_f.value = str(pos.latitude)
                    lon_f.value = str(pos.longitude)
                    page.snack_bar = ft.SnackBar(content=ft.Text(f"Coordenadas da Pista {idx+1} capturadas!"))
                    page.snack_bar.open = True
                    page.update()
                else:
                    page.snack_bar = ft.SnackBar(content=ft.Text("Não foi possível obter GPS. Verifique permissões."))
                    page.snack_bar.open = True
                    page.update()
            return capturar
        
        btn_capturar = ft.Button("📍 Capturar", on_click=fazer_captura(i, lat_field, lon_field))
        linha = ft.Row([lat_field, lon_field, btn_capturar], alignment="center", spacing=10)
        grupo = ft.Column([num_pista, linha], horizontal_alignment="center", spacing=10)
        grupos.controls.append(grupo)
        campos.append((lat_field, lon_field, btn_capturar))

    def iniciar_jogo(e):
        novas_pistas = []
        for i, (lat_f, lon_f, _) in enumerate(campos):
            try:
                lat = float(lat_f.value)
                lon = float(lon_f.value)
            except:
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Erro na Pista {i+1}: coordenada inválida!"))
                page.snack_bar.open = True
                page.update()
                return
            novas_pistas.append({
                "icone": pistas_existentes[i]["icone"],
                "lat": lat,
                "lon": lon,
            })
        
        # Abre a tela do jogo e obtém a função que inicia o bip após a fala
        # Precisamos passar o callback para falar()
        def apos_fala():
            # A tela_jogo já foi criada, mas precisamos do retorno da função que inicia o bip
            # Vamos armazenar a função retornada em uma variável fora do escopo atual
            nonlocal iniciar_bip_callback
            if iniciar_bip_callback:
                iniciar_bip_callback()
        
        # Primeiro criamos a tela do jogo, mas ela ainda não vai iniciar o bip
        # Ela retorna uma função que, quando chamada, inicia o bip
        iniciar_bip_callback = tela_jogo(page, novas_pistas)
        # Agora toca a mensagem e, ao terminar, chama o callback
        falar("Bem-vindo à caça ao tesouro do Theo. Theo, não se esqueça: sua família te ama!", callback=apos_fala)

    btn_iniciar = ft.Button("▶️ Iniciar Caça", on_click=iniciar_jogo, style=ft.ButtonStyle(bgcolor="#4CAF50", color="white"), width=200)

    layout = ft.Column(
        [titulo, subtitulo, ft.Divider(height=20), grupos, ft.Divider(height=30), btn_iniciar],
        horizontal_alignment="center",
        spacing=20,
    )
    page.add(layout)

# ------------------- MAIN -------------------
def main(page: ft.Page):
    tela_configuracao(page)

ft.app(target=main)