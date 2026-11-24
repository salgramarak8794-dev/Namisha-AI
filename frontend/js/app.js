document.addEventListener("DOMContentLoaded", () => {
  const canvas = document.getElementById("character-canvas");
  const rig = new AnimeCharacterRig(canvas);
  // Attempt to load Live2D model; fallback to sprite rig if unavailable
  let live2dRenderer = null;
  try {
    // Dynamically import the Live2D wrapper (must be included via script tag or bundler)
    live2dRenderer = new Live2DRenderer(canvas, "assets/live2d/placeholder.model3.json");
  } catch (e) {
    console.warn("Live2D renderer not available, using sprite rig", e);
    live2dRenderer = null;
  }
  function getRenderer(){
    return live2dRenderer || rig;
  }

  // UI Elements
  const statusDot = document.getElementById("status-dot");
  const micBtn = document.getElementById("mic-btn");
  const screenBtn = document.getElementById("screen-btn");
  const settingsBtn = document.getElementById("settings-btn");
  const chatInput = document.getElementById("chat-input");
  const sendBtn = document.getElementById("send-btn");
  const chatHistory = document.getElementById("chat-history");
  const resourceBadge = document.getElementById("resource-badge");
  const jealousBanner = document.getElementById("jealous-banner");
  const settingsModal = document.getElementById("settings-modal");
  const closeSettingsBtn = document.getElementById("close-settings-btn");
  const voiceStatusPill = document.getElementById("voice-status-pill");

  // Settings inputs
  const toggleJealous = document.getElementById("toggle-jealous");
  const toggleVoice = document.getElementById("toggle-voice");
  const toggleLightweight = document.getElementById("toggle-lightweight");
  const toggleContinuousVoice = document.getElementById("toggle-continuous-voice");
  const selectVoice = document.getElementById("select-voice");

  let ws = null;
  let isMuted = false;
  let screenPermGranted = false;
  let audioContext = null;
  let currentAudio = null;

  // Continuous Hands-Free Voice Conversation State
  let isContinuousVoiceActive = false;
  let isListening = false;
  let webSpeechRec = null;
  let useWebSpeech = false;

  // Emotion badge mappings
  const EMOTION_BADGES = {
    neutral: "🌸 Normal",
    happy: "✨ Happy!",
    smiling: "😊 Smiling",
    blushing: "😳 Blushing",
    shy: "🙈 Shy...",
    pouting: "🥺 Pout!",
    playfully_jealous: "😤 Hmph!",
    sad: "💧 Sad...",
    concerned: "🥺 Concerned",
    surprised: "😲 Surprised!",
    curious: "🧐 Curious",
    excited: "🎉 Excited!",
    sleepy: "💤 Sleepy...",
    thinking: "💭 Thinking...",
    laughing: "😆 Hehe!"
  };

  const characterCard = document.getElementById("character-card");
  const emotionBubble = document.getElementById("emotion-bubble");
  const voiceWaves = document.getElementById("voice-waves");

  function setVisualEmotion(exp) {
    if (rig) rig.setEmotion(exp);
    if (emotionBubble) emotionBubble.textContent = EMOTION_BADGES[exp] || `🌸 ${exp}`;
    if (characterCard) {
      characterCard.classList.remove(...Object.keys(EMOTION_BADGES));
      characterCard.classList.add(exp);
    }
  }

  function updateVoiceStatus(text, mode = "") {
    if (!voiceStatusPill) return;
    voiceStatusPill.textContent = text;
    voiceStatusPill.className = "voice-status-pill";
    if (mode) voiceStatusPill.classList.add(mode);
  }

  // Toggle floating mode – hides chat UI and enlarges avatar
function toggleFloatingMode(){
  document.body.classList.toggle('floating-mode');
  const isFloating = document.body.classList.contains('floating-mode');
  // Persist state (optional)
  sendWS({type:'floatToggle', enabled:isFloating});
}

  try {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      webSpeechRec = new SpeechRecognition();
      webSpeechRec.continuous = false;
      webSpeechRec.interimResults = true;
      webSpeechRec.lang = "en-US";

      webSpeechRec.onstart = () => {
        isListening = true;
        updateVoiceStatus("🎙️ Listening... speak naturally", "listening");
        statusDot.className = "status-dot listening";
      };

      webSpeechRec.onresult = (event) => {
        let interim = "";
        let final = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) final += event.results[i][0].transcript;
          else interim += event.results[i][0].transcript;
        }
        if (interim) {
          updateVoiceStatus(`Heard: "${interim.slice(-25)}"`, "listening");
        }
        if (final && final.trim()) {
          sendChatMessage(final.trim());
        }
      };

      webSpeechRec.onerror = (e) => {
        // Fall back to backend Faster-Whisper VAD
        useWebSpeech = false;
        isListening = false;
      };

      webSpeechRec.onend = () => {
        isListening = false;
      };

      useWebSpeech = true;
    }
  } catch (e) {
    useWebSpeech = false;
  }

  // 2. WebSocket Setup
  function connectWS() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      statusDot.className = "status-dot";
      console.log("Connected to Namisha Core Engine");
      sendWS({ type: "ping" });
      updateVoiceStatus("🎙️ Voice ready — click to chat");
    };

    ws.onmessage = (event) => {
      const data = jsonParseSafe(event.data);
      if (!data) return;

      switch (data.type) {
        case "expression_change":
          setVisualEmotion(data.expression);
          break;

        case "token":
          appendStreamingToken(data.token);
          break;

        case "audio_response":
          playAudioResponse(data.audio_url, data.expression);
          break;

        case "playful_jealous_greeting":
          handleJealousGreeting(data);
          break;

        case "stt_status":
          if (data.status === "listening") {
            isListening = true;
            statusDot.className = "status-dot listening";
            updateVoiceStatus("🎙️ Listening... speak naturally", "listening");
          } else {
            isListening = false;
            statusDot.className = "status-dot";
          }
          break;

        case "transcription_result":
          if (data.text) {
            updateVoiceStatus("Heard you! Thinking...", "speaking");
            sendChatMessage(data.text);
          } else {
            // Nothing spoken or silence
            if (isContinuousVoiceActive) {
              setTimeout(() => { triggerListening(); }, 600);
            } else {
              updateVoiceStatus("Voice ready", "");
            }
          }
          break;
      }
    };

    ws.onclose = () => {
      statusDot.className = "status-dot";
      setTimeout(connectWS, 2000);
    };
  }

  function sendWS(obj) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(obj));
    }
  }

  function jsonParseSafe(str) {
    try { return JSON.parse(str); } catch { return null; }
  }

  // 3. Audio Playback & Real-time Lip-Sync
  function playAudioResponse(audioUrl, expression) {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }

    if (expression) setVisualEmotion(expression);
    rig.setSpeaking(true);
    if (characterCard) characterCard.classList.add("speaking");
    if (voiceWaves) voiceWaves.style.display = "flex";
    updateVoiceStatus("🔊 Namisha is speaking...", "speaking");

    const audio = new Audio(audioUrl);
    currentAudio = audio;

    function onSpeechEnd() {
      rig.setSpeaking(false);
      setVisualEmotion("neutral");
      if (characterCard) characterCard.classList.remove("speaking");
      if (voiceWaves) voiceWaves.style.display = "none";

      // Hands-free continuous voice loop: auto-listen after Namisha finishes speaking
      if (isContinuousVoiceActive && !isMuted) {
        updateVoiceStatus("Listening for you...", "listening");
        setTimeout(() => {
          if (isContinuousVoiceActive && !isMuted) {
            triggerListening();
          }
        }, 450);
      } else {
        updateVoiceStatus("Voice ready", "");
      }
    }

    // Web Audio API for mouth movement
    try {
      if (!audioContext) audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const source = audioContext.createMediaElementSource(audio);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 64;
      source.connect(analyser);
      analyser.connect(audioContext.destination);

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      function checkAudio() {
        if (!audio.paused && !audio.ended) {
          analyser.getByteFrequencyData(dataArray);
          let sum = 0;
          for (let i = 0; i < bufferLength; i++) sum += dataArray[i];
          const avg = sum / bufferLength;
          rig.setAudioAmplitude(avg / 128.0);
          requestAnimationFrame(checkAudio);
        } else {
          onSpeechEnd();
        }
      }
      requestAnimationFrame(checkAudio);
    } catch (e) {
      audio.onended = onSpeechEnd;
    }

    audio.play().catch(e => {
      onSpeechEnd();
    });
  }

  // 4. Trigger Microphone Listening
  function triggerListening() {
    if (isListening) return;

    if (useWebSpeech && webSpeechRec) {
      try {
        webSpeechRec.start();
        return;
      } catch (e) {
        // Fall back to backend Faster-Whisper VAD
      }
    }

    sendWS({ type: "start_stt" });
  }

  // 5. Playful Jealous Voice-First Greeting
  function handleJealousGreeting(data) {
    jealousBanner.style.display = "block";
    jealousBanner.textContent = "Hmph! (Playful Jealous)";
    setTimeout(() => { jealousBanner.style.display = "none"; }, 3500);

    setVisualEmotion(data.expression || "playfully_jealous");
    if (data.audio_url) {
      playAudioResponse(data.audio_url, data.expression);
    }
  }

  // 6. Away / Return Detection
  let lastFocusTime = Date.now();
  window.addEventListener("focus", () => {
    const awaySec = (Date.now() - lastFocusTime) / 1000;
    if (awaySec > 10) {
      sendWS({ type: "user_return", away_seconds: awaySec });
    }
    lastFocusTime = Date.now();
  });
  window.addEventListener("blur", () => {
    lastFocusTime = Date.now();
  });

  // 7. Chat Interaction
  let currentAssistantBubble = null;

  function appendStreamingToken(token) {
    if (!currentAssistantBubble) {
      currentAssistantBubble = document.createElement("div");
      currentAssistantBubble.className = "chat-bubble assistant";
      chatHistory.appendChild(currentAssistantBubble);
    }
    currentAssistantBubble.textContent += token;
    chatHistory.scrollTop = chatHistory.scrollHeight;
  }

  function sendChatMessage(text) {
    const cleanText = text.trim();
    if (!cleanText) return;

    // Add user bubble
    const userBubble = document.createElement("div");
    userBubble.className = "chat-bubble user";
    userBubble.textContent = cleanText;
    chatHistory.appendChild(userBubble);
    chatHistory.scrollTop = chatHistory.scrollHeight;

    currentAssistantBubble = null;
    updateVoiceStatus("💭 Namisha is thinking...", "speaking");
    sendWS({ type: "user_message", message: cleanText });
    chatInput.value = "";
  }

  sendBtn.addEventListener("click", () => sendChatMessage(chatInput.value));
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendChatMessage(chatInput.value);
  });

  // 8. Hands-free Voice Chat Toggle Button
  micBtn.addEventListener("click", () => {
    isContinuousVoiceActive = !isContinuousVoiceActive;
    if (isContinuousVoiceActive) {
      micBtn.classList.add("active");
      micBtn.textContent = "🎙️ Voice Active";
      updateVoiceStatus("🎙️ Voice Chat ON — speak freely!", "listening");
      triggerListening();
    } else {
      micBtn.classList.remove("active");
      micBtn.textContent = "🎙️ Voice Chat";
      updateVoiceStatus("Voice Chat paused — click to talk", "");
      isListening = false;
      if (webSpeechRec) {
        try { webSpeechRec.stop(); } catch {}
      }
    }
  });

  // 9. Screen Awareness Toggle
  screenBtn.addEventListener("click", async () => {
    screenPermGranted = !screenPermGranted;
    screenBtn.classList.toggle("active", screenPermGranted);
    screenBtn.textContent = screenPermGranted ? "👁️ Screen: ON" : "👁️ Screen";
    rig.setEmotion(screenPermGranted ? "curious" : "neutral");
  });

  // 10. Settings Modal
  settingsBtn.addEventListener("click", async () => {
    settingsModal.style.display = "flex";
    const res = await fetch("/api/settings");
    const data = await res.json();
    toggleJealous.checked = data.playful_jealous_mode?.enabled ?? true;
    toggleVoice.checked = data.voice?.enabled ?? true;
    toggleLightweight.checked = data.general?.lightweight_mode ?? false;
    toggleContinuousVoice.checked = data.voice?.continuous_conversation ?? true;
    if (selectVoice && data.voice?.edge_tts_voice) {
      selectVoice.value = data.voice.edge_tts_voice;
    }
  });

  closeSettingsBtn.addEventListener("click", async () => {
    settingsModal.style.display = "none";
    const update = {
      playful_jealous_mode: { enabled: toggleJealous.checked },
      voice: {
        enabled: toggleVoice.checked,
        continuous_conversation: toggleContinuousVoice.checked,
        edge_tts_voice: selectVoice ? selectVoice.value : "en-US-JennyNeural"
      },
      general: { lightweight_mode: toggleLightweight.checked }
    };
    rig.setLightweightMode(toggleLightweight.checked);
    await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(update)
    });
  });

  // 11. Resource Telemetry Polling (Every 3.5s, very lightweight)
  setInterval(async () => {
    try {
      const res = await fetch("/api/status");
      const d = await res.json();
      resourceBadge.textContent = `CPU: ${d.cpu_percent}% | RAM: ${d.ram_used_gb}/${d.ram_total_gb} GB (${d.ram_percent}%) | ${d.active_model}`;
    } catch {}
  }, 3500);

  connectWS();
});
