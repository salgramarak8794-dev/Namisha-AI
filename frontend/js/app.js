document.addEventListener("DOMContentLoaded", () => {
  const canvas = document.getElementById("character-canvas");
  const rig = new AnimeCharacterRig(canvas);

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

  // Settings inputs
  const toggleJealous = document.getElementById("toggle-jealous");
  const toggleVoice = document.getElementById("toggle-voice");
  const toggleLightweight = document.getElementById("toggle-lightweight");
  const selectModel = document.getElementById("select-model");

  let ws = null;
  let isMuted = false;
  let screenPermGranted = false;
  let audioContext = null;
  let currentAudio = null;

  // 1. WebSocket Setup
  function connectWS() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      statusDot.className = "status-dot";
      console.log("Connected to Namisha Core Engine");
      sendWS({ type: "ping" });
    };

    ws.onmessage = (event) => {
      const data = jsonParseSafe(event.data);
      if (!data) return;

      switch (data.type) {
        case "expression_change":
          rig.setEmotion(data.expression);
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
            statusDot.className = "status-dot listening";
            micBtn.classList.add("active");
          } else {
            statusDot.className = "status-dot";
            micBtn.classList.remove("active");
          }
          break;

        case "transcription_result":
          sendChatMessage(data.text);
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

  // 2. Audio Playback & Real-time Lip-Sync
  function playAudioResponse(audioUrl, expression) {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }

    if (expression) rig.setEmotion(expression);
    rig.setSpeaking(true);

    const audio = new Audio(audioUrl);
    currentAudio = audio;

    // Use Web Audio API for real-time mouth movement
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
          rig.setSpeaking(false);
          rig.setEmotion("neutral");
        }
      }
      requestAnimationFrame(checkAudio);
    } catch (e) {
      // Fallback simple timer lip-sync
      audio.onended = () => {
        rig.setSpeaking(false);
        rig.setEmotion("neutral");
      };
    }

    audio.play().catch(e => {
      rig.setSpeaking(false);
    });
  }

  // 3. Playful Jealous Voice-First Greeting
  function handleJealousGreeting(data) {
    jealousBanner.style.display = "block";
    jealousBanner.textContent = "Hmph! (Playful Jealous)";
    setTimeout(() => { jealousBanner.style.display = "none"; }, 3500);

    rig.setEmotion(data.expression || "playfully_jealous");
    if (data.audio_url) {
      playAudioResponse(data.audio_url, data.expression);
    }
  }

  // 4. Away / Return Detection
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

  // 5. Chat Interaction
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
    sendWS({ type: "user_message", message: cleanText });
    chatInput.value = "";
  }

  sendBtn.addEventListener("click", () => sendChatMessage(chatInput.value));
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendChatMessage(chatInput.value);
  });

  // 6. Mic Voice Input Toggle
  micBtn.addEventListener("click", () => {
    sendWS({ type: "start_stt" });
  });

  // 7. Screen Awareness Toggle
  screenBtn.addEventListener("click", async () => {
    screenPermGranted = !screenPermGranted;
    screenBtn.classList.toggle("active", screenPermGranted);
    screenBtn.textContent = screenPermGranted ? "👁️ Screen: ON" : "👁️ Screen";
    rig.setEmotion(screenPermGranted ? "curious" : "neutral");
  });

  // 8. Settings Modal
  settingsBtn.addEventListener("click", async () => {
    settingsModal.style.display = "flex";
    const res = await fetch("/api/settings");
    const data = await res.json();
    toggleJealous.checked = data.playful_jealous_mode?.enabled ?? true;
    toggleVoice.checked = data.voice?.enabled ?? true;
    toggleLightweight.checked = data.general?.lightweight_mode ?? false;
  });

  closeSettingsBtn.addEventListener("click", async () => {
    settingsModal.style.display = "none";
    const update = {
      playful_jealous_mode: { enabled: toggleJealous.checked },
      voice: { enabled: toggleVoice.checked },
      general: { lightweight_mode: toggleLightweight.checked }
    };
    rig.setLightweightMode(toggleLightweight.checked);
    await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(update)
    });
  });

  // 9. Resource Telemetry Polling (Every 3.5s, very lightweight)
  setInterval(async () => {
    try {
      const res = await fetch("/api/status");
      const d = await res.json();
      resourceBadge.textContent = `CPU: ${d.cpu_percent}% | RAM: ${d.ram_used_gb}/${d.ram_total_gb} GB (${d.ram_percent}%) | ${d.active_model}`;
    } catch {}
  }, 3500);

  connectWS();
});
