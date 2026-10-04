/**
 * Audio & Alert Sound Synthesizer for D-SQUARE 2.0
 * Uses sossound folder alert sound (tithuh-warning-545568.mp3) for D-SQUARE GPT and Rescue GPT alerts.
 * Fallback to Web Audio API oscillators if audio element playback is restricted.
 */

const SOS_AUDIO_PATH = '/sossound/tithuh-warning-545568.mp3';

let sosAudioElement = null;
let audioCtx = null;
let isMuted = false;
let continuousAlarmInterval = null;

function getSosAudioElement() {
  if (typeof window === 'undefined') return null;
  if (!sosAudioElement) {
    sosAudioElement = new Audio(SOS_AUDIO_PATH);
    sosAudioElement.loop = true;
    sosAudioElement.preload = 'auto';
  }
  return sosAudioElement;
}

export function initAudioContext() {
  try {
    if (!audioCtx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) {
        audioCtx = new AudioContext();
      }
    }
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
  } catch (err) {
    console.warn("Web Audio API initialization notice:", err);
  }
}

export function setAudioMuted(muted) {
  isMuted = muted;
  if (isMuted && sosAudioElement) {
    try {
      sosAudioElement.pause();
    } catch (e) {
      // ignore
    }
  }
}

export function getAudioMuted() {
  return isMuted;
}

export function playDispatchBeep(frequency = 880, type = 'sine', duration = 0.25) {
  if (isMuted) return;

  try {
    initAudioContext();
    if (!audioCtx) return;

    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.type = type;
    osc.frequency.value = frequency;

    const now = audioCtx.currentTime;
    gain.gain.setValueAtTime(0.3, now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);

    osc.connect(gain);
    gain.connect(audioCtx.destination);

    osc.start(now);
    osc.stop(now + duration);
  } catch (err) {
    console.warn("Audio playback error:", err);
  }
}

export function playSosAlarmBeepsFallback() {
  if (isMuted) return;
  try {
    initAudioContext();
    playDispatchBeep(880, 'sine', 0.2);
    setTimeout(() => playDispatchBeep(1046.5, 'triangle', 0.25), 220);
    setTimeout(() => playDispatchBeep(1318.5, 'sine', 0.3), 450);
  } catch (err) {
    console.warn("SOS Alarm Beep fallback error:", err);
  }
}

export function playSosAlarmBeeps() {
  if (isMuted) return;
  try {
    const audioEl = getSosAudioElement();
    if (audioEl) {
      audioEl.currentTime = 0;
      audioEl.loop = false;
      const promise = audioEl.play();
      if (promise !== undefined) {
        promise.catch(err => {
          console.warn("sossound playback fallback:", err);
          playSosAlarmBeepsFallback();
        });
      }
    } else {
      playSosAlarmBeepsFallback();
    }
  } catch (err) {
    playSosAlarmBeepsFallback();
  }
}

export function startContinuousSosAlarm() {
  if (isMuted) return;

  try {
    const audioEl = getSosAudioElement();
    if (audioEl) {
      audioEl.currentTime = 0;
      audioEl.loop = true;
      const promise = audioEl.play();
      if (promise !== undefined) {
        promise.catch(err => {
          console.warn("sossound loop playback notice (falling back to beep interval):", err);
          playSosAlarmBeepsFallback();
          if (!continuousAlarmInterval) {
            continuousAlarmInterval = setInterval(() => {
              if (!isMuted) playSosAlarmBeepsFallback();
            }, 1200);
          }
        });
      }
    } else {
      playSosAlarmBeepsFallback();
      if (!continuousAlarmInterval) {
        continuousAlarmInterval = setInterval(() => {
          if (!isMuted) playSosAlarmBeepsFallback();
        }, 1200);
      }
    }
  } catch (err) {
    console.warn("Continuous sossound alert error:", err);
    playSosAlarmBeepsFallback();
  }
}

export function stopContinuousSosAlarm() {
  if (sosAudioElement) {
    try {
      sosAudioElement.pause();
      sosAudioElement.currentTime = 0;
    } catch (e) {
      // ignore
    }
  }
  if (continuousAlarmInterval) {
    clearInterval(continuousAlarmInterval);
    continuousAlarmInterval = null;
  }
}

export function isContinuousSosAlarmActive() {
  if (sosAudioElement && !sosAudioElement.paused) {
    return true;
  }
  return Boolean(continuousAlarmInterval);
}
