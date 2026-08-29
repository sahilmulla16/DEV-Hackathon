import React, { useState, useEffect } from "react";
import { supabase } from "../lib/supabaseClient";
import "./Auth.css";

export default function Auth({ onLogin, onClose }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSignup, setIsSignup] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  /* ─── ESC KEY CLOSE ───────────────────────── */
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === "Escape") onClose();
    };

    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, [onClose]);

  /* ─── AUTH HANDLER ───────────────────────── */
  const handleAuth = async () => {
    if (!email || !password) {
      setErrorMsg("Please enter email and password");
      return;
    }

    setLoading(true);
    setErrorMsg("");
    setSuccessMsg("");

    try {
      let res;

      /* ─── SIGNUP FLOW ─────────────────────── */
      if (isSignup) {
        const { error } = await supabase.auth.signUp({
            email,
            password,
        });

        if (error) throw error;

        setSuccessMsg("Account created. Please login.");
        setIsSignup(false); // switch to login
        return;
        }

      /* ─── LOGIN FLOW ─────────────────────── */
      res = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (res.error) throw res.error;

      onLogin(res.data.user);

    } catch (err) {
      setErrorMsg(err.message || "Something went wrong");
    }

    setLoading(false);
  };

  return (
    <div className="auth-overlay" onClick={onClose}>
      <div
        className="auth-card"
        onClick={(e) => e.stopPropagation()}
      >
        {/* CLOSE BUTTON */}
        <button
          className="auth-close"
          onClick={onClose}
        >
          ✕
        </button>

        {/* HEADER */}
        <div className="auth-header">
          <h2>
            {isSignup ? "Create your account" : "Welcome back"}
          </h2>
          <p>
            {isSignup
              ? "Start using your AI Agent"
              : "Login to continue"}
          </p>
        </div>

        {/* FORM */}
        <div className="auth-form">
          <input
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <input
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          {/* ERROR */}
          {errorMsg && (
            <div className="auth-error">
              {errorMsg}
            </div>
          )}

          {/* SUCCESS */}
          {successMsg && (
            <div className="auth-success">
              {successMsg}
            </div>
          )}

          <button
            onClick={handleAuth}
            disabled={loading}
          >
            {loading
              ? "Processing..."
              : isSignup
              ? "Create Account"
              : "Login"}
          </button>
        </div>

        {/* SWITCH */}
        <div className="auth-switch">
          <span>
            {isSignup
              ? "Already have an account?"
              : "Don't have an account?"}
          </span>

          <button
            onClick={() => {
              setIsSignup(!isSignup);
              setErrorMsg("");
              setSuccessMsg("");
            }}
          >
            {isSignup ? "Login" : "Sign up"}
          </button>
        </div>
      </div>
    </div>
  );
}