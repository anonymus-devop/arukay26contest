import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView, ActivityIndicator } from 'react-native';
import { Droplets, Thermometer, Sun, BrainCircuit, CheckCircle2, LogIn, User } from 'lucide-react-native';
import { styled } from 'nativewind';
import * as AuthSession from 'expo-auth-session';
import { initializeApp } from 'firebase/app';
import { getDatabase, ref, onValue } from 'firebase/database';

const StyledView = styled(View);
const StyledText = styled(Text);

// ==========================================
// CONFIGURACIÓN CS ID (OAuth 2.1)
// ==========================================
const CS_ID_CONFIG = {
  clientId: 'TU_CLIENT_ID',
  redirectUri: AuthSession.makeRedirectUri(),
  authEndpoint: 'https://cmkumxprmmhuinxfppxl.supabase.co/auth/v1/oauth/authorize',
  tokenEndpoint: 'https://cmkumxprmmhuinxfppxl.supabase.co/auth/v1/oauth/token',
};

// ==========================================
// CONFIGURACIÓN FIREBASE
// ==========================================
const firebaseConfig = {
  apiKey: "AIzaSyD7MQGGDWKMn436YTfk0f_Wa7OO0TWM79c",
  authDomain: "arukaycontest26.firebaseapp.com",
  databaseURL: "https://arukaycontest26-default-rtdb.firebaseio.com",
  projectId: "arukaycontest26",
  storageBucket: "arukaycontest26.firebasestorage.app",
  messagingSenderId: "971257684252",
  appId: "1:971257684252:web:8ac2de748ca3f852f81ad9",
  measurementId: "G-KJDQ7H8WH4"
};

const app = initializeApp(firebaseConfig);
const db = getDatabase(app);

export default function App() {
  // ESTADOS DE AUTENTICACIÓN
  const [userToken, setUserToken] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [loadingAuth, setLoadingAuth] = useState(false);

  // ESTADOS DE SENSORES E IA
  const [loadingAI, setLoadingAI] = useState(false);
  const [aiResponse, setAiResponse] = useState('Esperando análisis...');
  const [sensors, setSensors] = useState({ humidity: 0, temp: 0, light: 0 });

  // 1. FLUJO DE LOGIN CS ID
  const handleLogin = async () => {
    setLoadingAuth(true);
    try {
      const result = await AuthSession.startAsync({
        authUrl: \\?client_id=\&redirect_uri=\&response_type=code&scope=openid profile email\,
        returnUrl: CS_ID_CONFIG.redirectUri,
      });

      if (result.type === 'success') {
        const { code } = result.params;
        // Intercambio de Código por Access Token
        const tokenResponse = await fetch(CS_ID_CONFIG.tokenEndpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({
            grant_type: 'authorization_code',
            client_id: CS_ID_CONFIG.clientId,
            code: code,
            redirect_uri: CS_ID_CONFIG.redirectUri,
          }),
        });
        const tokenData = await tokenResponse.json();
        setUserToken(tokenData.access_token);
        setUserProfile({ name: 'Usuario Huerto' }); // Simplificado
      }
    } catch (error) {
      console.error('Error en Auth:', error);
    } finally {
      setLoadingAuth(false);
    }
  };

  // 2. ESCUCHA DE SENSORES (SÓLO SI ESTÁ LOGUEADO)
  useEffect(() => {
    if (!userToken) return;
    const sensorsRef = ref(db, 'sensors/');
    const unsubscribe = onValue(sensorsRef, (snapshot) => {
      const data = snapshot.val();
      if (data) setSensors(data);
    });
    return () => unsubscribe();
  }, [userToken]);

  // 3. ANÁLISIS CON IA (USA EL TOKEN PARA BUSCAR API KEY EN SQL)
  const analyzeWithAI = async () => {
    setLoadingAI(true);
    try {
      // FLUJO LÓGICO:
      // 1. Usar userToken para consultar Firebase SQL (Data Connect) la API Key del usuario
      // 2. Hacer fetch a OpenAI/Gemini usando esa Key privada
      
      await new Promise(resolve => setTimeout(resolve, 1500)); 
      
      if (sensors.humidity < 40) {
        setAiResponse('?? La humedad está baja (\%). ¡Tus plantas necesitan agua!');
      } else if (sensors.temp > 30) {
        setAiResponse('?? Temperatura alta (\°C). ¡Cuidado con el sol directo!');
      } else {
        setAiResponse('? Todo está en orden. El huerto está saludable.');
      }
    } catch (error) {
      setAiResponse('Error al conectar con la IA.');
    } finally {
      setLoadingAI(false);
    }
  };

  // PANTALLA DE LOGIN
  if (!userToken) {
    return (
      <StyledView className='flex-1 bg-slate-50 justify-center p-6'>
        <StyledView className='items-center mb-12'>
          <StyledView className='bg-violet-100 p-6 rounded-full mb-6'>
            <BrainCircuit color='#8b5cf6' size={60} />
          </StyledView>
          <StyledText className='text-4xl font-bold text-slate-800 text-center'>Huerto AI</StyledText>
          <StyledText className='text-slate-500 text-center mt-2'>Toma decisiones inteligentes para tu cultivo</StyledText>
        </StyledView>

        <TouchableOpacity 
          onPress={handleLogin}
          disabled={loadingAuth}
          className='bg-violet-600 p-5 rounded-2xl flex-row items-center justify-center shadow-lg active:bg-violet-700'
        >
          {loadingAuth ? <ActivityIndicator color='white' /> : (
            <>
              <LogIn color='white' size={24} />
              <StyledText className='text-white font-bold text-lg ml-3'>Entrar con CS ID</StyledText>
            </>
          )}
        </TouchableOpacity>
        <StyledText className='text-center text-slate-400 mt-6 text-xs'>Autenticación segura vía OAuth 2.1</StyledText>
      </StyledView>
    );
  }

  // PANTALLA DE DASHBOARD
  return (
    <StyledView className='flex-1 bg-slate-50 p-6 pt-12'>
      <StyledView className='flex-row justify-between items-center mb-8'>
        <StyledView>
          <StyledText className='text-3xl font-bold text-slate-800'>Huerto AI ??</StyledText>
          <StyledView className='flex-row items-center'>
             <User color='#64748b' size={14} />
             <StyledText className='text-slate-500 ml-1 text-sm'>\{userProfile?.name\}</StyledText>
          </StyledView>
        </StyledView>
        <TouchableOpacity onPress={() => setUserToken(null)} className='bg-slate-200 p-3 rounded-full'>
           <StyledText className='text-slate-600 text-xs font-bold'>Salir</StyledText>
        </TouchableOpacity>
      </StyledView>

      <StyledView className='flex-row flex-wrap justify-between mb-8'>
        <SensorCard icon={<Droplets color='#3b82f6' size={24} />} label='Humedad' value={\\%\} color='bg-blue-100' />
        <SensorCard icon={<Thermometer color='#ef4444' size={24} />} label='Temperatura' value={\\°C\} color='bg-red-100' />
        <SensorCard icon={<Sun color='#f59e0b' size={24} />} label='Luz' value={\\ lx\} color='bg-yellow-100' />
      </StyledView>

      <StyledView className='bg-white p-6 rounded-3xl shadow-sm border border-slate-200'>
        <StyledView className='flex-row items-center mb-4'>
          <BrainCircuit color='#8b5cf6' size={28} />
          <StyledText className='text-xl font-semibold text-slate-800 ml-2'>Análisis de IA</StyledText>
        </StyledView>
        <StyledView className='bg-slate-100 p-4 rounded-2xl mb-6'>
          <StyledText className='text-slate-600 leading-6 italic'>
            {loadingAI ? 'La IA está analizando...' : aiResponse}
          </StyledText>
        </StyledView>
        <TouchableOpacity 
          onPress={analyzeWithAI}
          disabled={loadingAI}
          className='bg-violet-600 p-4 rounded-2xl items-center shadow-md active:bg-violet-700'
        >
          {loadingAI ? <ActivityIndicator color='white' /> : <StyledText className='text-white font-bold text-lg'>Consultar a la IA</StyledText>}
        </TouchableOpacity>
      </StyledView>

      <StyledView className='mt-auto flex-row items-center justify-center p-4 bg-green-100 rounded-full'>
        <CheckCircle2 color='#16a34a' size={18} />
        <StyledText className='text-green-700 text-sm ml-2 font-medium'>Sincronizado con el Micro:bit</StyledText>
      </StyledView>
    </StyledView>
  );
}

function SensorCard({ icon, label, value, color }) {
  return (
    <StyledView className={\w-[48%] \ p-4 rounded-3xl mb-4 border border-transparent\}>
      <StyledView className='flex-row justify-between items-start mb-2'>
        <StyledView className='bg-white p-2 rounded-xl shadow-sm'>
          {icon}
        </StyledView>
      </StyledView>
      <StyledText className='text-slate-600 text-sm font-medium'>\{label\}</StyledText>
      <StyledText className='text-slate-800 text-2xl font-bold'>\{value\}</StyledText>
    </StyledView>
  );
}
