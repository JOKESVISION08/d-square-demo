/**
 * Audio & Alert Sound Engine for D-SQUARE 2.0
 * Uses the sossound folder MP3 alert sound (/sossound/tithuh-warning-545568.mp3)
 * as the sole alert sound across D-SQUARE GPT, Rescue GPT, and all alert notifications.
 */

const SOS_AUDIO_PATH = '/sossound/tithuh-warning-545568.mp3';

let sosAudioElement = null;
let isMuted = false;
let continuousAlarmInterval = null;
let isAudioUnlocked = false;

function getSosAudioElement() {
  if (typeof window === 'undefined') return null;
  if (!sosAudioElement) {
    sosAudioElement = new Audio(SOS_AUDIO_PATH);
    sosAudioElement.preload = 'auto';
  }
  return sosAudioElement;
}

/**
 * Fallback Web Audio API synthesized SOS warning alarm beep
 */
function playSynthSosAlarm() {
  try {
    if (typeof window === 'undefined') return;
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(880, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.4);
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.4);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.4);
  } catch (e) {
    console.warn("Synth SOS audio fallback warning:", e);
  }
}

/**
 * Pre-loads audio and attaches global user gesture listeners to bypass browser autoplay restrictions
 */
export function initAudioContext() {
  if (typeof window === 'undefined') return;
  
  const unlock = () => {
    try {
      const audioEl = getSosAudioElement();
      if (audioEl) {
        audioEl.load();
        const promise = audioEl.play();
        if (promise !== undefined) {
          promise.then(() => {
            audioEl.pause();
            audioEl.currentTime = 0;
            isAudioUnlocked = true;
          }).catch(() => {
            // Silence initial autoplay restriction error
          });
        }
      }
    } catch (err) {
      console.warn("Audio unlock notice:", err);
    }
  };

  if (!isAudioUnlocked) {
    const events = ['click', 'touchstart', 'keydown', 'pointerdown'];
    const handler = () => {
      unlock();
      events.forEach(evt => window.removeEventListener(evt, handler, true));
    };
    events.forEach(evt => window.addEventListener(evt, handler, { capture: true, once: true }));
  }
}

// Auto-register unlock listeners on browser module load
if (typeof window !== 'undefined') {
  initAudioContext();
}

export function setAudioMuted(muted) {
  isMuted = muted;
  if (isMuted) {
    stopContinuousSosAlarm();
  }
}

export function getAudioMuted() {
  return isMuted;
}

/**
 * Plays the sossound alert sound once for single notifications or dispatches.
 */
export function playSosAlarmSound() {
  if (isMuted) return;

  try {
    initAudioContext();
    const audioEl = getSosAudioElement();
    if (audioEl) {
      audioEl.currentTime = 0;
      audioEl.loop = false;
      const promise = audioEl.play();
      if (promise !== undefined) {
        promise.catch(err => {
          console.warn("sossound audio play notice, triggering synth warning:", err);
          playSynthSosAlarm();
        });
      }
    } else {
      playSynthSosAlarm();
    }
  } catch (err) {
    console.warn("sossound alert error:", err);
    playSynthSosAlarm();
  }
}

// Alias playDispatchBeep & playSosAlarmBeeps to play default sossound alert sound
export const playDispatchBeep = playSosAlarmSound;
export const playSosAlarmBeeps = playSosAlarmSound;

/**
 * Plays the sossound alert sound on a continuous loop for active SOS alerts in D-SQUARE GPT & Rescue GPT.
 */
export function startContinuousSosAlarm() {
  if (isMuted) return;

  try {
    initAudioContext();
    const audioEl = getSosAudioElement();
    if (audioEl) {
      audioEl.currentTime = 0;
      audioEl.loop = true;
      const promise = audioEl.play();
      if (promise !== undefined) {
        promise.catch(err => {
          console.warn("sossound loop play notice (retrying via interval & synth):", err);
          playSynthSosAlarm();
          if (!continuousAlarmInterval) {
            continuousAlarmInterval = setInterval(() => {
              if (!isMuted) playSosAlarmSound();
            }, 1800);
          }
        });
      }
    } else {
      playSynthSosAlarm();
    }
  } catch (err) {
    console.warn("Continuous sossound alert error:", err);
    playSynthSosAlarm();
  }
}

/**
 * Stops continuous sossound alert sound and resets playback.
 */
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

