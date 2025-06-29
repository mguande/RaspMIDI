# 🔧 Solução de Problemas - Zoom G3X

## ❌ Problema: Zoom G3X não conecta

### 🔍 Diagnóstico
O erro `MidiOutWinMM::openPort: error creating Windows MM MIDI output port` indica que o Zoom G3X não está respondendo corretamente via MIDI.

### 💡 Soluções (em ordem de prioridade)

#### 1. ⚡ Alimentação Externa (MUITO IMPORTANTE)
**O Zoom G3X PRECISA de alimentação externa para funcionar via MIDI!**

- ✅ Conecte o adaptador de alimentação 9V ao Zoom G3X
- ✅ Certifique-se de que a fonte está ligada
- ✅ O LED de alimentação deve estar aceso
- ❌ **NÃO funciona apenas com USB**

#### 2. 🔌 Conexão USB
- ✅ Use cabo USB de qualidade
- ✅ Conecte diretamente ao computador (não via hub)
- ✅ Teste diferentes portas USB
- ✅ Verifique se o cabo não está danificado

#### 3. 🛠️ Drivers
- ✅ Instale os drivers mais recentes do Zoom G3X
- ✅ Baixe do site oficial da Zoom
- ✅ Reinicie o computador após instalar
- ✅ Verifique no Gerenciador de Dispositivos

#### 4. 🔄 Reinicialização
- ✅ Desligue o Zoom G3X
- ✅ Desconecte o USB
- ✅ Aguarde 10 segundos
- ✅ Reconecte o USB
- ✅ Ligue o Zoom G3X
- ✅ Reinicie o RaspMIDI

#### 5. 💻 Configurações do Windows
- ✅ Execute o RaspMIDI como Administrador
- ✅ Verifique se não há outros programas usando MIDI
- ✅ Feche DAWs, editores de patch, etc.
- ✅ Verifique firewall/antivírus

#### 6. 🎛️ Configurações do Zoom G3X
- ✅ Verifique se o MIDI está habilitado no Zoom
- ✅ Acesse: Menu → MIDI → MIDI Channel (deve ser 1)
- ✅ Verifique se não está em modo de edição
- ✅ Teste com o software oficial da Zoom primeiro

### 🧪 Teste Manual

1. **Teste com software oficial:**
   - Abra o Zoom G3X Edit
   - Verifique se conecta
   - Se conectar, o problema é no RaspMIDI
   - Se não conectar, é problema de hardware/drivers

2. **Verifique portas MIDI:**
   - Abra o Gerenciador de Dispositivos
   - Procure por "MIDI" ou "Zoom"
   - Deve aparecer "ZOOM G Series 3"

3. **Teste com outro software:**
   - Use um DAW (Reaper, FL Studio, etc.)
   - Configure o Zoom G3X como dispositivo MIDI
   - Teste se funciona

### 📋 Checklist de Verificação

- [ ] Zoom G3X ligado com alimentação externa
- [ ] LED de alimentação aceso
- [ ] Cabo USB conectado
- [ ] Drivers instalados
- [ ] Nenhum outro programa usando MIDI
- [ ] RaspMIDI executado como administrador
- [ ] Zoom G3X funcionando com software oficial
- [ ] Porta "ZOOM G Series 3" aparece no sistema

### 🆘 Se nada funcionar

1. **Teste em outro computador**
2. **Teste com outro cabo USB**
3. **Teste com outro adaptador de alimentação**
4. **Contate o suporte da Zoom**
5. **Verifique se o Zoom G3X não está com defeito**

### 📞 Logs para Análise

Se o problema persistir, forneça:
- Logs completos do RaspMIDI
- Screenshot do Gerenciador de Dispositivos
- Lista de portas MIDI disponíveis
- Versão do Windows
- Versão dos drivers do Zoom

### 🎯 Resumo

**O problema mais comum é a falta de alimentação externa.** O Zoom G3X não funciona via MIDI apenas com alimentação USB. Conecte sempre o adaptador 9V! 