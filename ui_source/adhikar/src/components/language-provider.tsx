import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import {
  LANGUAGES,
  dictionaries,
  isRtl,
  languageName,
  type LanguageCode,
  type TranslationKey,
} from "@/lib/i18n";

type LanguageContextValue = {
  language: LanguageCode;
  setLanguage: (code: LanguageCode) => void;
  t: (key: TranslationKey) => string;
  englishName: string;
  rtl: boolean;
};

const LanguageContext = createContext<LanguageContextValue | null>(null);
const STORAGE_KEY = "sahayak.language";

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<LanguageCode>("en");

  useEffect(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY) as LanguageCode | null;
    if (stored && LANGUAGES.some((l) => l.code === stored)) setLanguageState(stored);
  }, []);

  const setLanguage = useCallback((code: LanguageCode) => {
    setLanguageState(code);
    window.localStorage.setItem(STORAGE_KEY, code);
  }, []);

  const value = useMemo<LanguageContextValue>(() => {
    const dict = dictionaries[language] ?? dictionaries.en;
    return {
      language,
      setLanguage,
      t: (key: TranslationKey) => dict[key] ?? dictionaries.en[key],
      englishName: languageName(language),
      rtl: isRtl(language),
    };
  }, [language, setLanguage]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage(): LanguageContextValue {
  const context = useContext(LanguageContext);
  if (!context) throw new Error("useLanguage must be used inside LanguageProvider");
  return context;
}
