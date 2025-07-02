# Changelog - Correção dos Comandos SYSEX Zoom G3X

## 📅 Data: 28/06/2025

### 🎯 Objetivo
Corrigir os comandos SYSEX para Zoom G3X baseado na análise do projeto [JavaPedalMIDI](https://github.com/PedalController/JavaPedalMIDI).

### ❌ Problemas Identificados
1. **Device ID incorreto**: Usando `0x6E` (MS-50G+) em vez de `0x5A` (G3X)
2. **Comandos SYSEX incorretos**: Usando comandos de outros modelos Zoom
3. **Estrutura de comandos**: Não seguia o padrão correto da G3X
4. **Método `send_sysex_patch` faltando**: Não implementado no controller principal

### ✅ Correções Implementadas

#### 1. Arquivo: `app/midi/zoom_g3x.py`
- **Device ID**: Corrigido de `0x6E` para `0x5A`
- **Comandos SYSEX**: Atualizados com comandos corretos do JavaPedalMIDI
- **Novos métodos**:
  - `send_sysex_patch()`: Seleciona patch específico
  - `send_sysex_tuner()`: Controla afinador
  - `send_sysex_effect_block()`: Controla blocos de efeito
  - `_manipulate_effect()`: Manipula efeitos via SysEx
- **Constantes**: Adicionadas para tipos de comando (SET_STATUS, CHANGE_EFFECT, PARAM_EFFECT)

#### 2. Arquivo: `app/midi/controller.py`
- **Novo método**: `send_sysex_patch()` implementado
- **Integração**: Delega para controlador Zoom G3X quando apropriado
- **Fallback**: Comando SysEx genérico para outros dispositivos

#### 3. Arquivo: `app/api/midi_routes.py`
- **Rota `/sysex/tuner`**: Atualizada para usar controlador específico
- **Rota `/sysex/effect`**: Atualizada para usar controlador específico
- **Device ID**: Corrigido de `0x6E` para `0x5A` nos comandos genéricos
- **Mensagens**: Melhoradas com feedback mais específico

#### 4. Arquivo: `app/web/static/js/app.js`
- **Exemplos SysEx**: Atualizados com device ID correto (`0x5A`)
- **Função `sendZoomTuner`**: Atualizada para suportar ligar/desligar
- **Função `sendZoomEffect`**: Melhorada com mensagens mais específicas
- **Comandos automáticos**: Corrigidos para usar device ID correto

### 🔧 Comandos SYSEX Corretos

#### Comandos Básicos
| Função | Comando | Descrição |
|--------|---------|-----------|
| **Identity Request** | `F0 7E 7F 06 01 F7` | Solicita identificação |
| **Current Patch Number** | `F0 52 00 5A 33 F7` | Número do patch atual |
| **Current Patch Details** | `F0 52 00 5A 29 F7` | Detalhes do patch atual |
| **Specific Patch Details** | `F0 52 00 5A 09 00 00 <patch> F7` | Detalhes de patch específico |

#### Comandos de Sincronização
| Função | Comando | Descrição |
|--------|---------|-----------|
| **Lissen Me** | `F0 52 00 5A 50 F7` | Inicia comunicação |
| **You Can Talk** | `F0 52 00 5A 16 F7` | Finaliza comunicação |

#### Comandos de Controle
| Função | Comando | Descrição |
|--------|---------|-----------|
| **Set Effect Status** | `F0 52 00 5A 31 <effect> 00 <value> <value2> F7` | Liga/desliga efeito |
| **Change Effect Type** | `F0 52 00 5A 31 <effect> 01 <value> <value2> F7` | Muda tipo de efeito |
| **Set Effect Parameter** | `F0 52 00 5A 31 <effect> <param+2> <value> <value2> F7` | Define parâmetro |

#### Comandos Especiais
| Função | Comando | Descrição |
|--------|---------|-----------|
| **Tuner** | `F0 52 00 5A 64 0B F7` | Liga/desliga afinador |
| **Effect Block** | `F0 52 00 5A 64 03 00 <block> 00 00 <state> F7` | Controla bloco de efeito |

### 🧪 Testes

#### Script de Teste Criado
- **Arquivo**: `test_zoom_sysex_commands.py`
- **Função**: Testa todos os comandos SYSEX corretos
- **Cobertura**: Identity, Patch Details, Specific Patch, Tuner, Effect Block, Sync

#### Como Executar
```bash
python test_zoom_sysex_commands.py
```

### 📚 Documentação

#### Arquivos Criados/Atualizados
- **`ZOOM_G3X_SYSEX_COMMANDS.md`**: Documentação completa dos comandos
- **`CHANGELOG_SYSEX_FIX.md`**: Este arquivo de mudanças

### 🚨 Importante

#### Requisitos Obrigatórios
- **Alimentação externa 9V**: Obrigatória para funcionamento MIDI
- **Drivers**: Instalados e atualizados
- **Conexão USB**: Estável e direta (não via hub)

#### Troubleshooting
- **Erro de conexão**: Verificar alimentação externa
- **Comandos não funcionam**: Confirmar device ID (0x5A)
- **Respostas não recebidas**: Aguardar mais tempo (até 1 segundo)

### 🔄 Próximos Passos

1. **Testar** com Zoom G3X real
2. **Validar** respostas dos comandos
3. **Ajustar** timeouts se necessário
4. **Implementar** retry em caso de falha
5. **Adicionar** mais comandos específicos se necessário

### 📋 Status

- ✅ Device ID corrigido
- ✅ Comandos SYSEX atualizados
- ✅ Métodos implementados
- ✅ API atualizada
- ✅ Frontend atualizado
- ✅ Documentação criada
- ✅ Script de teste criado
- ⏳ Aguardando testes com hardware real 