/**
 * Namisha 2.0 — Parametric 2D Rigged Anime Character Engine
 * Optimized for low CPU/RAM on Ryzen 3 3250U.
 */

class AnimeCharacterRig {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    
    // Canvas sizing
    this.width = canvas.width;
    this.height = canvas.height;
    
    // Performance controls
    this.idleFps = 18;
    this.activeFps = 30;
    this.targetFps = this.idleFps;
    this.lastFrameTime = performance.now();
    this.isLightweight = false;
    this.isPaused = false;
    this.speaking = false;
    this.audioAmplitude = 0.0;
    
    // Dynamic Rig Parameters (Current values)
    this.params = {
      headTilt: 0,        // degrees
      headY: 0,           // breathing offset (px)
      eyeOpen: 1.0,       // 0 (closed) to 1 (wide)
      eyePupilX: 0,       // -1 to 1
      eyePupilY: 0,       // -1 to 1
      eyebrowHeight: 0,   // -1 to 1
      eyebrowAngle: 0,    // -1 (sad) to 1 (angry/determined)
      mouthOpen: 0.0,     // 0 (closed) to 1 (open for vowel)
      mouthSmile: 0.2,    // -1 (frown) to 1 (broad smile)
      mouthPout: 0.0,     // 0 to 1
      blush: 0.0,         // 0 to 1
      hairSway: 0         // wave angle
    };

    // Target parameters for smooth interpolation
    this.targets = Object.assign({}, this.params);
    
    // Blinking timer
    this.blinkTimer = 0;
    this.nextBlinkInterval = 3000 + Math.random() * 2000;
    this.isBlinking = false;
    this.blinkPhase = 0;

    // Mouse tracking for gaze
    this.mouseTarget = { x: 0, y: 0 };
    this.trackMouse = true;

    // Breathing clock
    this.clock = 0;

    this.currentEmotion = "neutral";
    this.setEmotion("neutral");

    this.bindEvents();
    this.startLoop();
  }

  setLightweightMode(enabled) {
    this.isLightweight = enabled;
    this.idleFps = enabled ? 12 : 18;
    this.activeFps = enabled ? 22 : 30;
    this.targetFps = this.speaking ? this.activeFps : this.idleFps;
  }

  setAudioAmplitude(amp) {
    this.audioAmplitude = Math.max(0, Math.min(1, amp));
    if (this.speaking) {
      // Modulate mouth opening based on audio amplitude
      this.targets.mouthOpen = 0.1 + this.audioAmplitude * 0.85;
    }
  }

  setSpeaking(speaking) {
    this.speaking = speaking;
    this.targetFps = speaking ? this.activeFps : this.idleFps;
    if (!speaking) {
      this.targets.mouthOpen = 0.0;
      this.audioAmplitude = 0.0;
    }
  }

  setEmotion(emotionName) {
    this.currentEmotion = emotionName;
    const t = this.targets;

    switch (emotionName) {
      case "happy":
        t.headTilt = 4;
        t.eyeOpen = 0.9;
        t.eyebrowHeight = 0.3;
        t.eyebrowAngle = 0.1;
        t.mouthSmile = 0.8;
        t.mouthPout = 0.0;
        t.blush = 0.3;
        break;

      case "smiling":
        t.headTilt = 2;
        t.eyeOpen = 0.95;
        t.eyebrowHeight = 0.2;
        t.eyebrowAngle = 0.0;
        t.mouthSmile = 0.6;
        t.mouthPout = 0.0;
        t.blush = 0.2;
        break;

      case "blushing":
        t.headTilt = -3;
        t.eyeOpen = 0.85;
        t.eyebrowHeight = 0.1;
        t.eyebrowAngle = -0.1;
        t.mouthSmile = 0.4;
        t.mouthPout = 0.0;
        t.blush = 0.9;
        break;

      case "shy":
        t.headTilt = -5;
        t.eyeOpen = 0.75;
        t.eyebrowHeight = -0.1;
        t.eyebrowAngle = -0.2;
        t.mouthSmile = 0.2;
        t.mouthPout = 0.1;
        t.blush = 0.7;
        t.eyePupilY = 0.4;
        break;

      case "pouting":
        t.headTilt = -6;
        t.eyeOpen = 0.8;
        t.eyebrowHeight = -0.3;
        t.eyebrowAngle = -0.4;
        t.mouthSmile = -0.4;
        t.mouthPout = 0.8;
        t.blush = 0.4;
        break;

      case "playfully_jealous":
        t.headTilt = -7;
        t.eyeOpen = 0.75;
        t.eyebrowHeight = -0.2;
        t.eyebrowAngle = -0.3;
        t.mouthSmile = -0.3;
        t.mouthPout = 0.9;
        t.blush = 0.6;
        t.eyePupilX = 0.3;
        break;

      case "sad":
        t.headTilt = -2;
        t.eyeOpen = 0.7;
        t.eyebrowHeight = -0.4;
        t.eyebrowAngle = -0.5;
        t.mouthSmile = -0.6;
        t.mouthPout = 0.2;
        t.blush = 0.0;
        break;

      case "concerned":
        t.headTilt = 3;
        t.eyeOpen = 0.9;
        t.eyebrowHeight = -0.3;
        t.eyebrowAngle = -0.3;
        t.mouthSmile = -0.2;
        t.mouthPout = 0.1;
        t.blush = 0.1;
        break;

      case "surprised":
        t.headTilt = 0;
        t.eyeOpen = 1.0;
        t.eyebrowHeight = 0.6;
        t.eyebrowAngle = 0.2;
        t.mouthSmile = 0.0;
        t.mouthOpen = 0.5;
        t.mouthPout = 0.0;
        t.blush = 0.2;
        break;

      case "curious":
        t.headTilt = 8;
        t.eyeOpen = 0.95;
        t.eyebrowHeight = 0.4;
        t.eyebrowAngle = 0.1;
        t.mouthSmile = 0.3;
        t.mouthPout = 0.0;
        t.blush = 0.1;
        break;

      case "excited":
        t.headTilt = 5;
        t.eyeOpen = 1.0;
        t.eyebrowHeight = 0.5;
        t.eyebrowAngle = 0.2;
        t.mouthSmile = 0.9;
        t.mouthPout = 0.0;
        t.blush = 0.5;
        break;

      case "sleepy":
        t.headTilt = -4;
        t.eyeOpen = 0.45;
        t.eyebrowHeight = -0.2;
        t.eyebrowAngle = -0.1;
        t.mouthSmile = 0.1;
        t.mouthPout = 0.0;
        t.blush = 0.1;
        break;

      case "thinking":
        t.headTilt = 6;
        t.eyeOpen = 0.85;
        t.eyePupilX = 0.5;
        t.eyePupilY = -0.5;
        t.eyebrowHeight = 0.2;
        t.eyebrowAngle = 0.1;
        t.mouthSmile = 0.1;
        t.mouthPout = 0.2;
        t.blush = 0.0;
        break;

      case "laughing":
        t.headTilt = 6;
        t.eyeOpen = 0.2;
        t.eyebrowHeight = 0.4;
        t.eyebrowAngle = 0.2;
        t.mouthSmile = 1.0;
        t.mouthOpen = 0.6;
        t.mouthPout = 0.0;
        t.blush = 0.5;
        break;

      case "neutral":
      default:
        t.headTilt = 0;
        t.eyeOpen = 1.0;
        t.eyePupilX = 0;
        t.eyePupilY = 0;
        t.eyebrowHeight = 0.0;
        t.eyebrowAngle = 0.0;
        t.mouthSmile = 0.2;
        t.mouthOpen = 0.0;
        t.mouthPout = 0.0;
        t.blush = 0.15;
        break;
    }
  }

  bindEvents() {
    window.addEventListener("mousemove", (e) => {
      if (!this.trackMouse) return;
      const rect = this.canvas.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 3;
      const dx = (e.clientX - cx) / (rect.width / 2);
      const dy = (e.clientY - cy) / (rect.height / 2);
      this.mouseTarget.x = Math.max(-1, Math.min(1, dx));
      this.mouseTarget.y = Math.max(-1, Math.min(1, dy));
    });
  }

  lerp(start, end, factor) {
    return start + (end - start) * factor;
  }

  update(dt) {
    this.clock += dt * 0.002;

    // 1. Natural Breathing & Hair physics
    const breathRate = this.isLightweight ? 1.0 : 1.5;
    this.targets.headY = Math.sin(this.clock * breathRate) * 3;
    this.targets.hairSway = Math.sin(this.clock * 1.2) * 4;

    // 2. Mouse gaze follow (interpolated)
    if (this.currentEmotion !== "thinking" && this.currentEmotion !== "sleepy") {
      this.targets.eyePupilX = this.mouseTarget.x * 0.4;
      this.targets.eyePupilY = this.mouseTarget.y * 0.3;
    }

    // 3. Natural Blinking logic
    this.blinkTimer += dt;
    if (!this.isBlinking && this.blinkTimer > this.nextBlinkInterval) {
      this.isBlinking = true;
      this.blinkPhase = 0;
      this.blinkTimer = 0;
      this.nextBlinkInterval = 2500 + Math.random() * 3000;
    }

    if (this.isBlinking) {
      this.blinkPhase += dt * 0.008;
      if (this.blinkPhase < 1.0) {
        // Eyelid closing then opening: 1 -> 0 -> 1
        const closeFactor = Math.sin(this.blinkPhase * Math.PI);
        this.params.eyeOpen = Math.max(0, this.targets.eyeOpen * (1 - closeFactor));
      } else {
        this.isBlinking = false;
        this.params.eyeOpen = this.targets.eyeOpen;
      }
    } else {
      this.params.eyeOpen = this.lerp(this.params.eyeOpen, this.targets.eyeOpen, 0.15);
    }

    // 4. Interpolate all other parameters smoothly
    const lerpSpeed = 0.12;
    for (const key in this.params) {
      if (key !== "eyeOpen") {
        this.params[key] = this.lerp(this.params[key], this.targets[key], lerpSpeed);
      }
    }
  }

  render() {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    const centerX = this.width / 2;
    const centerY = this.height / 2 + 10 + this.params.headY;

    ctx.save();
    ctx.translate(centerX, centerY);
    ctx.rotate((this.params.headTilt * Math.PI) / 180);

    // --- Back Hair ---
    ctx.fillStyle = "#4a2a6e";
    ctx.beginPath();
    // Left twin-tail / side volume
    ctx.ellipse(-85 + this.params.hairSway, 70, 45, 95, 0.2, 0, Math.PI * 2);
    ctx.fill();
    // Right twin-tail
    ctx.beginPath();
    ctx.ellipse(85 + this.params.hairSway, 70, 45, 95, -0.2, 0, Math.PI * 2);
    ctx.fill();

    // --- Shoulders & Cute Collar ---
    ctx.fillStyle = "#2c1d3f";
    ctx.beginPath();
    ctx.ellipse(0, 130, 80, 40, 0, 0, Math.PI * 2);
    ctx.fill();

    // Neck
    ctx.fillStyle = "#ffeedd";
    ctx.beginPath();
    ctx.rect(-16, 60, 32, 35);
    ctx.fill();

    // --- Face Contour ---
    ctx.fillStyle = "#fff5ea";
    ctx.beginPath();
    ctx.moveTo(-58, 0);
    ctx.bezierCurveTo(-58, 60, -25, 78, 0, 84); // Chin
    ctx.bezierCurveTo(25, 78, 58, 60, 58, 0);
    ctx.bezierCurveTo(58, -50, -58, -50, -58, 0);
    ctx.fill();

    // Cute Anime Ears
    ctx.fillStyle = "#ffe6d5";
    ctx.beginPath();
    ctx.ellipse(-60, 10, 8, 14, -0.2, 0, Math.PI * 2);
    ctx.ellipse(60, 10, 8, 14, 0.2, 0, Math.PI * 2);
    ctx.fill();

    // --- Cheeks Blush ---
    if (this.params.blush > 0.05) {
      ctx.fillStyle = `rgba(255, 120, 150, ${this.params.blush * 0.7})`;
      ctx.beginPath();
      ctx.ellipse(-38, 25, 15, 8, 0.1, 0, Math.PI * 2);
      ctx.ellipse(38, 25, 15, 8, -0.1, 0, Math.PI * 2);
      ctx.fill();
    }

    // --- Eyebrows ---
    ctx.strokeStyle = "#5a326b";
    ctx.lineWidth = 3;
    ctx.lineCap = "round";
    const browY = -18 - this.params.eyebrowHeight * 8;
    const browAng = this.params.eyebrowAngle * 8;
    
    // Left Brow
    ctx.beginPath();
    ctx.moveTo(-45, browY + browAng);
    ctx.quadraticCurveTo(-32, browY - 4, -18, browY - browAng);
    ctx.stroke();

    // Right Brow
    ctx.beginPath();
    ctx.moveTo(18, browY - browAng);
    ctx.quadraticCurveTo(32, browY - 4, 45, browY + browAng);
    ctx.stroke();

    // --- Eyes ---
    this.renderEye(ctx, -32, 5, -1);
    this.renderEye(ctx, 32, 5, 1);

    // --- Nose ---
    ctx.fillStyle = "#e0a58a";
    ctx.beginPath();
    ctx.ellipse(0, 26, 2, 2.5, 0, 0, Math.PI * 2);
    ctx.fill();

    // --- Mouth ---
    this.renderMouth(ctx, 0, 48);

    // --- Front Hair & Bangs ---
    ctx.fillStyle = "#673ab7";
    ctx.beginPath();
    // Main hair dome
    ctx.ellipse(0, -25, 68, 55, 0, Math.PI, Math.PI * 2);
    ctx.fill();

    // Cute Anime Bangs
    ctx.beginPath();
    ctx.moveTo(-65, -25);
    ctx.quadraticCurveTo(-40, 5, -30, -5);   // Left strand
    ctx.quadraticCurveTo(-15, 15, 0, -8);     // Center strand
    ctx.quadraticCurveTo(15, 15, 30, -5);     // Right-center strand
    ctx.quadraticCurveTo(40, 5, 65, -25);     // Right strand
    ctx.closePath();
    ctx.fill();

    // Hair shine highlight
    ctx.strokeStyle = "rgba(255, 255, 255, 0.35)";
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.arc(0, -32, 45, -Math.PI * 0.75, -Math.PI * 0.25);
    ctx.stroke();

    ctx.restore();
  }

  renderEye(ctx, x, y, side) {
    ctx.save();
    ctx.translate(x, y);

    const eyeScaleY = Math.max(0.05, this.params.eyeOpen);

    // Eyelid clipping path
    ctx.beginPath();
    ctx.ellipse(0, 0, 18, 16 * eyeScaleY, 0, 0, Math.PI * 2);
    ctx.clip();

    // Sclera (Eye White)
    ctx.fillStyle = "#ffffff";
    ctx.fill();

    // Iris (Deep Violet to Amethyst gradient)
    const pupilX = this.params.eyePupilX * 6;
    const pupilY = this.params.eyePupilY * 4;
    const grad = ctx.createLinearGradient(0, -14, 0, 14);
    grad.addColorStop(0, "#311b92");
    grad.addColorStop(0.6, "#7b1fa2");
    grad.addColorStop(1, "#ba68c8");

    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.ellipse(pupilX, pupilY, 11, 14 * eyeScaleY, 0, 0, Math.PI * 2);
    ctx.fill();

    // Pupil
    ctx.fillStyle = "#1a0826";
    ctx.beginPath();
    ctx.ellipse(pupilX, pupilY + 1, 5, 6 * eyeScaleY, 0, 0, Math.PI * 2);
    ctx.fill();

    // Anime Light Reflections
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.ellipse(pupilX - 3 * side, pupilY - 4 * eyeScaleY, 3.5, 3.5 * eyeScaleY, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(pupilX + 3 * side, pupilY + 4 * eyeScaleY, 2, 2 * eyeScaleY, 0, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();

    // Eyelash Line
    ctx.strokeStyle = "#2e124d";
    ctx.lineWidth = 3.5;
    ctx.beginPath();
    ctx.ellipse(x, y - 8 * eyeScaleY, 18, 5 * eyeScaleY, 0, Math.PI * 0.85, Math.PI * 2.15);
    ctx.stroke();
  }

  renderMouth(ctx, x, y) {
    ctx.save();
    ctx.translate(x, y);

    const open = Math.max(0, this.params.mouthOpen);
    const smile = this.params.mouthSmile;
    const pout = this.params.mouthPout;

    if (pout > 0.4) {
      // Pouting mouth: small protruding 'o' with blush
      ctx.fillStyle = "#ff6f91";
      ctx.strokeStyle = "#7b1fa2";
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      ctx.ellipse(0, 0, 6, 6 + pout * 3, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    } else if (open > 0.15) {
      // Open mouth (speaking / laughing / surprised)
      ctx.fillStyle = "#9c27b0";
      ctx.strokeStyle = "#4a148c";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.ellipse(0, 0, 10 + smile * 3, open * 14, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      // Cute anime tongue
      ctx.fillStyle = "#ff80ab";
      ctx.beginPath();
      ctx.ellipse(0, open * 6, 7, open * 6, 0, 0, Math.PI);
      ctx.fill();
    } else {
      // Closed expressive curve (smile or neutral)
      ctx.strokeStyle = "#5a2d75";
      ctx.lineWidth = 2.5;
      ctx.lineCap = "round";
      ctx.beginPath();
      ctx.moveTo(-10, -smile * 3);
      ctx.quadraticCurveTo(0, smile * 6, 10, -smile * 3);
      ctx.stroke();
    }

    ctx.restore();
  }

  startLoop() {
    const loop = (currentTime) => {
      requestAnimationFrame(loop);
      if (this.isPaused) return;

      const dt = currentTime - this.lastFrameTime;
      const interval = 1000 / this.targetFps;

      if (dt >= interval) {
        this.lastFrameTime = currentTime - (dt % interval);
        this.update(dt);
        this.render();
      }
    };
    requestAnimationFrame(loop);
  }
}

window.AnimeCharacterRig = AnimeCharacterRig;
