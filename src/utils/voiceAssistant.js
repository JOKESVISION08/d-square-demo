/**
 * Web Speech API Voice Assistant Utility for D-SQUARE 2.0
 * Provides Speech-to-Text (STT Voice Input) and Text-to-Speech (TTS Voice Readout)
 * for D-SQUARE GPT and Rescue GPT standalone portals.
 */

let activeUtterance = null;

/**
 * Reads text out loud using browser SpeechSynthesis API.
 */
export function speakText(text, onEnd = () => {}, onError = () => {}) {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
    onError("Browser does not support Speech Synthesis API");
    return;
  }

  try {
    // Stop any ongoing speech
    window.speechSynthesis.cancel();

    // Clean text by stripping Markdown symbols and emojis for natural speech
    const cleanText = text
      .replace(/[*_~`#|]/g, '')
      .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '')
      .trim();

    if (!cleanText) return;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.lang = 'en-US';

    utterance.onend = () => {
      activeUtterance = null;
      onEnd();
    };

    utterance.onerror = (err) => {
      activeUtterance = null;
      console.warn("Speech Synthesis error:", err);
      onError(err);
    };

    activeUtterance = utterance;
    window.speechSynthesis.speak(utterance);
  } catch (err) {
    console.warn("Voice readout error:", err);
    onError(err);
  }
}

/**
 * Stops current active voice readout.
 */
export function stopSpeaking() {
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    try {
      window.speechSynthesis.cancel();
      activeUtterance = null;
    } catch (e) {
      // ignore
    }
  }
}

/**
 * Returns true if speech synthesis is currently active.
 */
export function isCurrentlySpeaking() {
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    return window.speechSynthesis.speaking;
  }
  return false;
}

/**
 * Initializes Web Speech Recognition (Mic Voice Input).
 */
export function startVoiceRecognition({ onResult, onError, onEnd, lang = 'en-US' }) {
  if (typeof window === 'undefined') return null;

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    onError("Speech Recognition API is not supported in this browser. Try Chrome, Edge, or Safari.");
    return null;
  }

  try {
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = lang;

    recognition.onresult = (event) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      onResult(transcript);
    };

    recognition.onerror = (event) => {
      console.warn("Speech Recognition notice:", event.error);
      onError(event.error);
    };

    recognition.onend = () => {
      onEnd();
    };

    recognition.start();
    return recognition;
  } catch (err) {
    console.warn("Failed to start voice recognition:", err);
    onError(err.message);
    return null;
  }
}
