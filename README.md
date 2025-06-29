# RaspMIDI 🎵

**Controlador MIDI para Zoom G3X e MVAVE Chocolate Plus**

Um sistema completo para controle MIDI de dispositivos de guitarra, permitindo gerenciamento de patches, efeitos e comandos MIDI através de uma interface web moderna.

## 🎸 Dispositivos Suportados

- **Zoom G3X** - Processador de efeitos para guitarra
- **MVAVE Chocolate Plus** - Controlador MIDI de pedal

## ✨ Funcionalidades

### 🎛️ Gerenciamento de Patches
- Criação e edição de patches MIDI
- Configuração de efeitos por patch
- Suporte a diferentes tipos de comandos (PC, CC, Note On/Off)
- Interface visual intuitiva

### 🔧 Controle de Efeitos
- Configuração individual de 6 efeitos
- Estados ligado/desligado por patch
- Visualização em tempo real

### 📡 Monitoramento MIDI
- Monitor em tempo real de comandos MIDI
- Log de comandos enviados
- Simulação de comandos para teste

### 🔌 Gerenciamento de Dispositivos
- Detecção automática de dispositivos
- Status de conexão em tempo real
- Reconexão automática
- Alertas de alimentação externa

### 🎚️ Comandos Especiais
- Comandos SysEx para Zoom G3X
- Afinador integrado
- Controle de blocos de efeitos
- Comandos personalizados

## 🚀 Instalação

### Pré-requisitos
- Python 3.8+
- pip
- Git

### Passos de Instalação

1. **Clone o repositório**
   ```bash
   git clone https://github.com/mguande/RaspMIDI.git
   cd RaspMIDI
   ```

2. **Crie um ambiente virtual**
   ```bash
   python -m venv venv
   ```

3. **Ative o ambiente virtual**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

4. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure o banco de dados**
   ```bash
   python -c "from app.database.database import init_db; init_db()"
   ```

6. **Execute o aplicativo**
   ```bash
   python run.py
   ```

7. **Acesse a interface web**
   ```
   http://localhost:5000
   ```

## 📁 Estrutura do Projeto

```
RaspMIDI/
├── app/                    # Aplicação principal
│   ├── api/               # Rotas da API REST
│   ├── bluetooth/         # Controle Bluetooth
│   ├── cache/             # Gerenciamento de cache
│   ├── database/          # Banco de dados
│   ├── midi/              # Controle MIDI
│   └── web/               # Interface web
│       ├── static/        # CSS, JS, imagens
│       └── templates/     # Templates HTML
├── data/                  # Dados do sistema
├── logs/                  # Logs da aplicação
├── docs/                  # Documentação
└── requirements.txt       # Dependências Python
```

## 🎮 Como Usar

### 1. Configuração Inicial
- Conecte os dispositivos MIDI via USB
- Acesse a interface web
- Configure os dispositivos de entrada e saída

### 2. Criação de Patches
- Clique em "Novo Patch"
- Configure nome, dispositivos e parâmetros
- Para Zoom G3X: selecione banco e patch
- Para Chocolate: configure canal de entrada

### 3. Configuração de Efeitos
- Habilite "Configuração de Efeitos"
- Configure cada efeito individualmente
- Salve o patch

### 4. Monitoramento
- Use o monitor MIDI para ver comandos em tempo real
- Teste comandos com a simulação
- Verifique logs de comandos enviados

## 🔧 Configuração

### Arquivo de Configuração
Crie um arquivo `config.json` na raiz do projeto:

```json
{
  "midi": {
    "input_device": "Chocolate MIDI In",
    "output_device": "Zoom G3X MIDI Out"
  },
  "bluetooth": {
    "enabled": true
  },
  "cache": {
    "timeout": 300
  }
}
```

### Variáveis de Ambiente
- `FLASK_ENV`: Ambiente (development/production)
- `FLASK_DEBUG`: Modo debug (True/False)
- `DATABASE_PATH`: Caminho do banco de dados

## 🐛 Troubleshooting

### Problemas Comuns

1. **Dispositivo não detectado**
   - Verifique conexão USB
   - Reinicie o aplicativo
   - Verifique drivers MIDI

2. **Comandos não funcionam**
   - Verifique configuração de dispositivos
   - Teste com monitor MIDI
   - Verifique alimentação externa (Zoom G3X)

3. **Interface não carrega**
   - Verifique se o servidor está rodando
   - Verifique logs de erro
   - Limpe cache do navegador

## 📝 Logs

Os logs são salvos em `logs/` com formato:
```
raspmidi_YYYYMMDD_HHMMSS.log
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Autor

**mguande** - [GitHub](https://github.com/mguande)

## 🙏 Agradecimentos

- Comunidade MIDI
- Desenvolvedores das bibliotecas utilizadas
- Testadores e contribuidores

---

**RaspMIDI** - Transformando sua experiência MIDI! 🎵
