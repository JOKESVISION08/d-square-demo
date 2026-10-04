import { initializeApp } from "firebase/app";
import { getAuth, connectAuthEmulator } from "firebase/auth";
import { getDatabase, connectDatabaseEmulator } from "firebase/database";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyDemoPlaceholderKey123456789",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "d-sqaure.firebaseapp.com",
  databaseURL: import.meta.env.VITE_FIREBASE_DATABASE_URL || "https://d-sqaure-default-rtdb.firebaseio.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "d-sqaure",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "d-sqaure.appspot.com",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "1234567890",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:1234567890:web:abcdef123456"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const database = getDatabase(app);

let isUsingEmulator = false;

// Default mode is REAL PRODUCTION MODE.
// Emulator connects ONLY when explicitly enabled via VITE_USE_FIREBASE_EMULATOR="true"
const useEmulator = import.meta.env.VITE_USE_FIREBASE_EMULATOR === 'true';

if (useEmulator && !window._firebaseEmulatorsConnected) {
  try {
    connectAuthEmulator(auth, "http://localhost:9099", { disableWarnings: true });
    connectDatabaseEmulator(database, "localhost", 9000);
    window._firebaseEmulatorsConnected = true;
    isUsingEmulator = true;
    console.log("🛠️ [EMULATOR MODE] Connected to Local Firebase Emulator Suite (Auth: 9099 | RTDB: 9000)");
  } catch (err) {
    console.warn("Firebase emulator connection notice:", err.message);
  }
} else {
  console.log("🌐 [PRODUCTION MODE] Connected to Production Firebase Realtime Database:", firebaseConfig.databaseURL);
}

export const isConfigured = Boolean(import.meta.env.VITE_FIREBASE_DATABASE_URL || firebaseConfig.databaseURL);

export { app, auth, database, isUsingEmulator, firebaseConfig };
