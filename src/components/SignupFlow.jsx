/**
 * SEC-021: Enterprise Self-Service Signup Flow
 *
 * Banking-Level Security Features:
 * - reCAPTCHA v3 integration
 * - Email verification
 * - Terms & privacy acceptance
 * - Progress tracking
 *
 * Flow:
 * 1. Sign Up Form
 * 2. Email Verification (check email)
 * 3. Organization Setup (auto after verification)
 * 4. Onboarding Complete
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Building2,
  Mail,
  User,
  Lock,
  Check,
  ArrowRight,
  ArrowLeft,
  Loader2,
  AlertCircle,
  CheckCircle,
  Shield,
  ExternalLink
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'https://pilot.owkai.app';
const RECAPTCHA_SITE_KEY = import.meta.env.VITE_RECAPTCHA_SITE_KEY || '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'; // Test key

/**
 * Signup Flow Component
 */
const SignupFlow = () => {
  // Form state
  const [step, setStep] = useState(1); // 1: Form, 2: Verify Email, 3: Complete
  const [formData, setFormData] = useState({
    email: '',
    firstName: '',
    lastName: '',
    phone: '',
    organizationName: '',
    organizationSize: '',
    industry: '',
    requestedTier: 'pilot',
    termsAccepted: false,
    privacyAccepted: false,
    marketingConsent: false
  });

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [signupId, setSignupId] = useState(null);
  const [verificationSent, setVerificationSent] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);

  // reCAPTCHA ref
  const recaptchaRef = useRef(null);

  // Load reCAPTCHA script
  useEffect(() => {
    const script = document.createElement('script');
    script.src = `https://www.google.com/recaptcha/api.js?render=${RECAPTCHA_SITE_KEY}`;
    script.async = true;
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, []);

  // Resend cooldown timer
  useEffect(() => {
    if (resendCooldown > 0) {
      const timer = setTimeout(() => setResendCooldown(resendCooldown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendCooldown]);

  // Get reCAPTCHA token
  const getRecaptchaToken = async () => {
    return new Promise((resolve) => {
      if (window.grecaptcha) {
        window.grecaptcha.ready(async () => {
          const token = await window.grecaptcha.execute(RECAPTCHA_SITE_KEY, { action: 'signup' });
          resolve(token);
        });
      } else {
        // Fallback for development
        resolve('test_token');
      }
    });
  };

  // Handle form input change
  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    setError('');
  };

  // Submit signup form
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Validate required fields
      if (!formData.email || !formData.firstName || !formData.lastName || !formData.organizationName) {
        throw new Error('Please fill in all required fields');
      }

      if (!formData.termsAccepted || !formData.privacyAccepted) {
        throw new Error('You must accept the Terms of Service and Privacy Policy');
      }

      // Get reCAPTCHA token
      const captchaToken = await getRecaptchaToken();

      // SEC-021: Build request body with only defined values (Pydantic v2 strict validation)
      const urlParams = new URLSearchParams(window.location.search);
      const requestBody = {
        // Required fields
        email: formData.email,
        first_name: formData.firstName,
        last_name: formData.lastName,
        organization_name: formData.organizationName,
        terms_accepted: formData.termsAccepted,
        privacy_accepted: formData.privacyAccepted,
        marketing_consent: formData.marketingConsent,
        captcha_token: captchaToken,
        requested_tier: formData.requestedTier || 'pilot'
      };

      // Optional fields - only include if they have values
      if (formData.phone) requestBody.phone = formData.phone;
      if (formData.organizationSize) requestBody.organization_size = formData.organizationSize;
      if (formData.industry) requestBody.industry = formData.industry;
      if (urlParams.get('utm_source')) requestBody.utm_source = urlParams.get('utm_source');
      if (urlParams.get('utm_medium')) requestBody.utm_medium = urlParams.get('utm_medium');
      if (urlParams.get('utm_campaign')) requestBody.utm_campaign = urlParams.get('utm_campaign');

      // Submit to API
      const response = await fetch(`${API_BASE}/api/signup/request`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      const data = await response.json();

      if (!response.ok) {
        // SEC-021: Handle different error formats from FastAPI
        let errorMessage = 'Signup failed. Please try again.';
        if (data.detail) {
          if (typeof data.detail === 'string') {
            errorMessage = data.detail;
          } else if (Array.isArray(data.detail)) {
            // FastAPI validation error format: [{loc: [...], msg: "...", type: "..."}]
            errorMessage = data.detail.map(e => e.msg || e.message || String(e)).join(', ');
          } else if (typeof data.detail === 'object' && data.detail.msg) {
            errorMessage = data.detail.msg;
          } else {
            errorMessage = JSON.stringify(data.detail);
          }
        } else if (data.message) {
          errorMessage = data.message;
        }
        throw new Error(errorMessage);
      }

      // Success - move to verification step
      setSignupId(data.signup_id);
      setVerificationSent(true);
      setStep(2);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Resend verification email
  const handleResendVerification = async () => {
    if (resendCooldown > 0) return;

    setLoading(true);
    setError('');

    try {
      const captchaToken = await getRecaptchaToken();

      const response = await fetch(`${API_BASE}/api/signup/resend-verification`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: formData.email,
          captcha_token: captchaToken
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to resend verification email');
      }

      setResendCooldown(60); // 60 second cooldown

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Subscription tier options
  const tiers = [
    { id: 'pilot', name: 'Pilot', description: 'Free 14-day trial', price: 'Free' },
    { id: 'growth', name: 'Growth', description: 'For growing teams', price: '$499/mo' },
    { id: 'enterprise', name: 'Enterprise', description: 'For large organizations', price: '$1,999/mo' }
  ];

  // Organization size options
  const orgSizes = [
    { value: '1-10', label: '1-10 employees' },
    { value: '11-50', label: '11-50 employees' },
    { value: '51-200', label: '51-200 employees' },
    { value: '201-500', label: '201-500 employees' },
    { value: '500+', label: '500+ employees' }
  ];

  // Industry options
  const industries = [
    { value: 'technology', label: 'Technology' },
    { value: 'finance', label: 'Finance & Banking' },
    { value: 'healthcare', label: 'Healthcare' },
    { value: 'retail', label: 'Retail & E-commerce' },
    { value: 'manufacturing', label: 'Manufacturing' },
    { value: 'consulting', label: 'Consulting' },
    { value: 'government', label: 'Government' },
    { value: 'education', label: 'Education' },
    { value: 'other', label: 'Other' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white">
            ASCEND<span className="text-blue-500">™</span>
          </h1>
          <p className="text-slate-400 mt-2">AI Governance Platform</p>
        </div>

        {/* Progress Steps */}
        <div className="flex justify-center mb-8">
          <div className="flex items-center space-x-4">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${step >= 1 ? 'bg-blue-600' : 'bg-slate-700'}`}>
              <User className="w-5 h-5 text-white" />
            </div>
            <div className={`w-16 h-1 ${step >= 2 ? 'bg-blue-600' : 'bg-slate-700'}`} />
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${step >= 2 ? 'bg-blue-600' : 'bg-slate-700'}`}>
              <Mail className="w-5 h-5 text-white" />
            </div>
            <div className={`w-16 h-1 ${step >= 3 ? 'bg-blue-600' : 'bg-slate-700'}`} />
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${step >= 3 ? 'bg-blue-600' : 'bg-slate-700'}`}>
              <CheckCircle className="w-5 h-5 text-white" />
            </div>
          </div>
        </div>

        {/* Card */}
        <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-xl p-8">

          {/* Step 1: Sign Up Form */}
          {step === 1 && (
            <form onSubmit={handleSubmit}>
              <h2 className="text-2xl font-bold text-white mb-2">Create your account</h2>
              <p className="text-slate-400 mb-6">Start your 14-day free trial. No credit card required.</p>

              {/* Error Message */}
              {error && (
                <div className="bg-red-900/30 border border-red-700 rounded-lg p-3 mb-4 flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-red-400" />
                  <span className="text-red-400 text-sm">{error}</span>
                </div>
              )}

              {/* Name Fields */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">First Name *</label>
                  <input
                    type="text"
                    name="firstName"
                    value={formData.firstName}
                    onChange={handleInputChange}
                    required
                    className="w-full px-4 py-2.5 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="John"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Last Name *</label>
                  <input
                    type="text"
                    name="lastName"
                    value={formData.lastName}
                    onChange={handleInputChange}
                    required
                    className="w-full px-4 py-2.5 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Doe"
                  />
                </div>
              </div>

              {/* Email */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-slate-300 mb-1">Work Email *</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-2.5 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="john@company.com"
                />
              </div>

              {/* Organization Name */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-slate-300 mb-1">Organization Name *</label>
                <input
                  type="text"
                  name="organizationName"
                  value={formData.organizationName}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-2.5 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Acme Corporation"
                />
              </div>

              {/* Organization Size & Industry */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Organization Size</label>
                  <select
                    name="organizationSize"
                    value={formData.organizationSize}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2.5 bg-slate-900/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select size</option>
                    {orgSizes.map(size => (
                      <option key={size.value} value={size.value}>{size.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Industry</label>
                  <select
                    name="industry"
                    value={formData.industry}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2.5 bg-slate-900/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select industry</option>
                    {industries.map(ind => (
                      <option key={ind.value} value={ind.value}>{ind.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* SEC-021: Terms & Privacy Checkboxes - Banking-Level Defense in Depth */}
              {/* HTML5 required + aria-required for browser-native validation + accessibility */}
              <div className="space-y-3 mb-6">
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    name="termsAccepted"
                    checked={formData.termsAccepted}
                    onChange={handleInputChange}
                    required
                    aria-required="true"
                    className="mt-1 w-4 h-4 rounded border-slate-600 bg-slate-900/50 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-slate-300">
                    I agree to the{' '}
                    <a href="/terms" target="_blank" className="text-blue-400 hover:underline">Terms of Service</a>
                    {' '}*
                  </span>
                </label>

                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    name="privacyAccepted"
                    checked={formData.privacyAccepted}
                    onChange={handleInputChange}
                    required
                    aria-required="true"
                    className="mt-1 w-4 h-4 rounded border-slate-600 bg-slate-900/50 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-slate-300">
                    I agree to the{' '}
                    <a href="/privacy" target="_blank" className="text-blue-400 hover:underline">Privacy Policy</a>
                    {' '}*
                  </span>
                </label>

                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    name="marketingConsent"
                    checked={formData.marketingConsent}
                    onChange={handleInputChange}
                    className="mt-1 w-4 h-4 rounded border-slate-600 bg-slate-900/50 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-slate-300">
                    Send me product updates and news (optional)
                  </span>
                </label>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-all disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  <>
                    Start Free Trial
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </button>

              {/* Login Link */}
              <p className="text-center text-slate-400 mt-4 text-sm">
                Already have an account?{' '}
                <a href="/login" className="text-blue-400 hover:underline">Sign in</a>
              </p>

              {/* Security Badge */}
              <div className="flex items-center justify-center gap-2 mt-6 pt-6 border-t border-slate-700">
                <Shield className="w-4 h-4 text-green-500" />
                <span className="text-xs text-slate-400">SOC 2 Type II Certified | GDPR Compliant</span>
              </div>
            </form>
          )}

          {/* Step 2: Verify Email */}
          {step === 2 && (
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <Mail className="w-8 h-8 text-blue-400" />
              </div>

              <h2 className="text-2xl font-bold text-white mb-2">Check your email</h2>
              <p className="text-slate-400 mb-6">
                We've sent a verification link to<br />
                <span className="text-white font-medium">{formData.email}</span>
              </p>

              <div className="bg-slate-900/50 border border-slate-600 rounded-lg p-4 mb-6">
                <p className="text-sm text-slate-300">
                  Click the link in the email to verify your account and complete setup.
                  The link expires in 24 hours.
                </p>
              </div>

              {/* Resend Button */}
              <button
                onClick={handleResendVerification}
                disabled={loading || resendCooldown > 0}
                className="text-blue-400 hover:text-blue-300 text-sm font-medium disabled:opacity-50"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Sending...
                  </span>
                ) : resendCooldown > 0 ? (
                  `Resend in ${resendCooldown}s`
                ) : (
                  'Resend verification email'
                )}
              </button>

              {error && (
                <div className="mt-4 text-red-400 text-sm">{error}</div>
              )}

              {/* Back Button */}
              <button
                onClick={() => setStep(1)}
                className="mt-6 text-slate-400 hover:text-white text-sm flex items-center gap-1 mx-auto"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to sign up
              </button>
            </div>
          )}

          {/* Step 3: Complete */}
          {step === 3 && (
            <div className="text-center">
              <div className="w-16 h-16 bg-green-600/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle className="w-8 h-8 text-green-400" />
              </div>

              <h2 className="text-2xl font-bold text-white mb-2">You're all set!</h2>
              <p className="text-slate-400 mb-6">
                Your organization has been created and you're ready to start using ASCEND.
              </p>

              <a
                href="/login"
                className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold rounded-lg transition-all"
              >
                Go to Dashboard
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center mt-6">
          <p className="text-slate-500 text-xs">
            By signing up, you agree to our Terms of Service and Privacy Policy.
            <br />
            &copy; 2025 Ascend Technologies, Inc. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
};

export default SignupFlow;
