import React, { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from 'react-native';

const API_BASE_URL = (typeof process !== 'undefined' && process.env?.EXPO_PUBLIC_API_URL)
  || 'https://arukay26contest.onrender.com';

const DEFAULT_SIMULATOR = { humidity: '512', temperature: '24', light: '140' };

function parseSensorText(value) {
  const raw = value.trim();
  if (!raw) throw new Error('Escribe una lectura primero.');
  if (raw.startsWith('{')) {
    const parsed = JSON.parse(raw);
    const data = { humidity: Number(parsed.humidity), temperature: Number(parsed.temperature ?? parsed.temp), light: Number(parsed.light) };
    if (Object.values(data).some((item) => !Number.isFinite(item))) throw new Error('El JSON debe tener humidity, temperature y light numéricos.');
    return data;
  }
  const values = raw.split(/[,;\s]+/).map(Number);
  if (values.length !== 3 || values.some((item) => !Number.isFinite(item))) throw new Error('Usa el formato humedad,temperatura,luz.');
  return { humidity: values[0], temperature: values[1], light: values[2] };
}

function formatDate(value) {
  if (!value) return 'Sin lectura';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString('es-CO');
}

export default function App() {
  const [dark, setDark] = useState(false);
  const [provider, setProvider] = useState('openai');
  const [apiKey, setApiKey] = useState('');
  const [deviceToken, setDeviceToken] = useState('');
  const [sensorText, setSensorText] = useState('512,24,140');
  const [simulator, setSimulator] = useState(DEFAULT_SIMULATOR);
  const [sensors, setSensors] = useState(null);
  const [advice, setAdvice] = useState('Conecta la Micro:bit o prueba el simulador.');
  const [adviceSource, setAdviceSource] = useState('GAIrden');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('Comprobando conexión…');

  const colors = useMemo(() => (dark ? DARK_COLORS : COLORS), [dark]);

  async function request(path, options = {}) {
    const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers: { Accept: 'application/json', ...(options.headers || {}) } });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || payload.error || `Error HTTP ${response.status}`);
    return payload;
  }

  function applyReading(data) {
    const normalized = { ...data, updated_at: data.updated_at || new Date().toISOString() };
    setSensors(normalized);
    setSensorText(`${normalized.humidity},${normalized.temperature},${normalized.light}`);
  }

  async function loadSensors() {
    setLoading(true);
    try {
      const payload = await request('/api/sensors');
      if (payload.data) { applyReading(payload.data); setStatus('Firebase conectado'); } else setStatus('Sin lecturas');
    } catch (error) { setStatus('Backend no disponible'); }
    finally { setLoading(false); }
  }

  async function analyze() {
    let data;
    try { data = parseSensorText(sensorText); } catch (error) { Alert.alert('Datos inválidos', error.message); return; }
    const providerHeader = provider === 'gemini' ? 'X-Gemini-Key' : 'X-OpenAI-Key';
    const headers = { 'Content-Type': 'application/json', 'X-AI-Provider': provider, ...(apiKey.trim() ? { [providerHeader]: apiKey.trim() } : {}) };
    setLoading(true);
    try {
      const payload = await request('/analizar', { method: 'POST', headers, body: JSON.stringify(data) });
      applyReading(payload.data);
      setAdvice(payload.consejo || 'No llegó un consejo.');
      setAdviceSource(payload.source === 'rules' ? 'Reglas locales' : `Generado por ${provider}`);
      setStatus('Análisis completado');
    } catch (error) { Alert.alert('No se pudo analizar', error.message); }
    finally { setLoading(false); }
  }

  function simulate() {
    const data = { humidity: Number(simulator.humidity), temperature: Number(simulator.temperature), light: Number(simulator.light) };
    if (Object.values(data).some((value) => !Number.isFinite(value))) { Alert.alert('Datos inválidos', 'Completa los tres valores del simulador.'); return; }
    applyReading(data);
    setStatus('Simulación lista');
  }

  useEffect(() => { loadSensors(); }, []);
  const attention = sensors && (sensors.temperature < 12 || sensors.temperature > 32 || sensors.humidity < 350 || sensors.humidity > 850);

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: colors.background }]}>
      <StatusBar barStyle={dark ? 'light-content' : 'dark-content'} />
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.header}>
          <View style={styles.brandRow}><View style={[styles.logo, { backgroundColor: colors.green }]}><Text style={styles.logoText}>🌿</Text></View><View><Text style={[styles.eyebrow, { color: colors.green }]}>GAIrden</Text><Text style={[styles.brand, { color: colors.text }]}>Tu jardín, más inteligente</Text></View></View>
          <View style={styles.headerActions}><Text style={[styles.status, { color: colors.muted }]}>{status}</Text><Switch value={dark} onValueChange={setDark} trackColor={{ false: '#c7d8ca', true: colors.green }} /></View>
        </View>

        <View style={[styles.hero, { backgroundColor: colors.card }]}><Text style={[styles.eyebrow, { color: colors.green }]}>PANEL DE CULTIVO</Text><Text style={[styles.title, { color: colors.text }]}>Hola, cuidador del huerto.</Text><Text style={[styles.subtitle, { color: colors.muted }]}>Usa datos de tu Micro:bit o simula una lectura para recibir una recomendación.</Text><View style={styles.row}><Pressable style={[styles.button, { backgroundColor: colors.green }]} onPress={loadSensors} disabled={loading}>{loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Actualizar</Text>}</Pressable><Pressable style={[styles.button, styles.secondary, { borderColor: colors.line }]} onPress={analyze} disabled={loading}><Text style={[styles.secondaryText, { color: colors.green }]}>Analizar AI</Text></Pressable></View></View>

        <View style={[styles.advice, { backgroundColor: dark ? '#214333' : '#17352a' }]}><Text style={styles.badge}>CONSEJO DE GAIRDEN</Text><Text style={styles.adviceTitle}>{adviceSource}</Text><Text style={styles.adviceText}>{advice}</Text></View>

        <View style={styles.metrics}><Metric label="Humedad" value={sensors?.humidity ?? '—'} unit="/ 1023" icon="💧" colors={colors} /><Metric label="Temperatura" value={sensors ? `${sensors.temperature}°` : '—'} unit="Celsius" icon="☀️" colors={colors} /><Metric label="Luz" value={sensors?.light ?? '—'} unit="/ 255" icon="🌤️" colors={colors} /></View>

        <View style={[styles.card, { backgroundColor: colors.card }]}><Text style={[styles.eyebrow, { color: colors.green }]}>DATOS PARA LA IA</Text><Text style={[styles.sectionTitle, { color: colors.text }]}>Lectura real o simulada</Text><Text style={[styles.help, { color: colors.muted }]}>Formato: 512,24,140 o JSON con humidity, temperature y light.</Text><TextInput value={sensorText} onChangeText={setSensorText} placeholder="512,24,140" placeholderTextColor={colors.muted} style={[styles.input, { color: colors.text, borderColor: colors.line, backgroundColor: colors.input }]} /><View style={styles.providerRow}><Pressable onPress={() => setProvider('openai')} style={[styles.provider, provider === 'openai' && { backgroundColor: colors.green }]}><Text style={[styles.providerText, { color: provider === 'openai' ? '#fff' : colors.text }]}>OpenAI</Text></Pressable><Pressable onPress={() => setProvider('gemini')} style={[styles.provider, provider === 'gemini' && { backgroundColor: colors.green }]}><Text style={[styles.providerText, { color: provider === 'gemini' ? '#fff' : colors.text }]}>Gemini</Text></Pressable></View><TextInput value={apiKey} onChangeText={setApiKey} placeholder="API key opcional" placeholderTextColor={colors.muted} secureTextEntry style={[styles.input, { color: colors.text, borderColor: colors.line, backgroundColor: colors.input }]} /><Text style={[styles.help, { color: colors.muted }]}>La clave solo se usa para esta solicitud y no se guarda.</Text><Pressable style={[styles.button, { backgroundColor: colors.green }]} onPress={analyze}><Text style={styles.buttonText}>Usar estos datos</Text></Pressable></View>

        <View style={[styles.card, { backgroundColor: colors.card }]}><Text style={[styles.eyebrow, { color: colors.green }]}>SIMULADOR MICRO:BIT</Text><Text style={[styles.sectionTitle, { color: colors.text }]}>Prueba sin hardware</Text>{[['humidity', 'Humedad (0–1023)'], ['temperature', 'Temperatura °C'], ['light', 'Luz (0–255)']].map(([key, label]) => <View key={key} style={styles.fieldRow}><Text style={[styles.fieldLabel, { color: colors.muted }]}>{label}</Text><TextInput keyboardType="numeric" value={simulator[key]} onChangeText={(value) => setSimulator({ ...simulator, [key]: value })} style={[styles.smallInput, { color: colors.text, borderColor: colors.line, backgroundColor: colors.input }]} /></View>)}<Pressable style={[styles.button, { backgroundColor: colors.green }]} onPress={simulate}><Text style={styles.buttonText}>Cargar simulación</Text></Pressable></View>

        <View style={[styles.card, { backgroundColor: colors.card }]}><Text style={[styles.eyebrow, { color: colors.green }]}>CONEXIÓN</Text><Text style={[styles.sectionTitle, { color: colors.text }]}>{attention ? 'Necesita atención' : sensors ? 'Huerto equilibrado' : 'Sin datos todavía'}</Text><Text style={[styles.help, { color: colors.muted }]}>Última lectura: {formatDate(sensors?.updated_at)}</Text><TextInput value={deviceToken} onChangeText={setDeviceToken} placeholder="Token del dispositivo" placeholderTextColor={colors.muted} secureTextEntry style={[styles.input, { color: colors.text, borderColor: colors.line, backgroundColor: colors.input }]} /><Text style={[styles.help, { color: colors.muted }]}>En Android XR/Meta Horizon OS usa `bridge.py` para conectar la Micro:bit y enviar lecturas a Flask.</Text></View>
      </ScrollView>
    </SafeAreaView>
  );
}

function Metric({ label, value, unit, icon, colors }) { return <View style={[styles.metric, { backgroundColor: colors.card, borderColor: colors.line }]}><View style={styles.metricHeader}><Text style={[styles.metricLabel, { color: colors.muted }]}>{label}</Text><Text style={styles.metricIcon}>{icon}</Text></View><Text style={[styles.metricValue, { color: colors.text }]}>{value}</Text><Text style={[styles.metricUnit, { color: colors.muted }]}>{unit}</Text></View>; }

const COLORS = { background: '#f5f7ef', card: '#ffffff', input: '#f8fbf6', text: '#17352a', muted: '#6b8077', green: '#2d8a63', line: '#e2eadf' };
const DARK_COLORS = { background: '#101a15', card: '#18261e', input: '#22372b', text: '#e5f2e7', muted: '#a8bdae', green: '#78c995', line: '#2d4436' };

const styles = StyleSheet.create({
  safe: { flex: 1 }, container: { width: '100%', maxWidth: 900, alignSelf: 'center', padding: 20, gap: 14 }, header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginBottom: 6 }, brandRow: { flexDirection: 'row', alignItems: 'center', gap: 10 }, logo: { width: 46, height: 46, borderRadius: 15, alignItems: 'center', justifyContent: 'center' }, logoText: { fontSize: 25 }, eyebrow: { fontSize: 11, fontWeight: '800', letterSpacing: 1.4 }, brand: { fontSize: 15, fontWeight: '800' }, headerActions: { alignItems: 'flex-end', gap: 4 }, status: { fontSize: 11, maxWidth: 150, textAlign: 'right' }, hero: { borderRadius: 24, padding: 24, gap: 10 }, title: { fontSize: 31, fontWeight: '900', letterSpacing: -1 }, subtitle: { fontSize: 15, lineHeight: 22, maxWidth: 620 }, row: { flexDirection: 'row', flexWrap: 'wrap', gap: 9, marginTop: 8 }, button: { minHeight: 46, borderRadius: 12, paddingHorizontal: 18, alignItems: 'center', justifyContent: 'center' }, buttonText: { color: '#fff', fontSize: 14, fontWeight: '800' }, secondary: { backgroundColor: 'transparent', borderWidth: 1 }, secondaryText: { fontSize: 14, fontWeight: '800' }, advice: { borderRadius: 24, padding: 24, gap: 9 }, badge: { alignSelf: 'flex-start', backgroundColor: '#b8dc72', color: '#17352a', borderRadius: 99, paddingHorizontal: 10, paddingVertical: 6, fontSize: 10, fontWeight: '900', letterSpacing: 1 }, adviceTitle: { color: '#fff', fontSize: 21, fontWeight: '900' }, adviceText: { color: '#d3e5d8', lineHeight: 23, fontSize: 16 }, metrics: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 }, metric: { flex: 1, minWidth: 150, borderRadius: 18, padding: 17, borderWidth: 1 }, metricHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }, metricLabel: { fontSize: 12, fontWeight: '800' }, metricIcon: { fontSize: 22 }, metricValue: { fontSize: 31, fontWeight: '900', marginTop: 13 }, metricUnit: { fontSize: 11, marginTop: 2 }, card: { borderRadius: 20, padding: 21, gap: 10 }, sectionTitle: { fontSize: 20, fontWeight: '900' }, help: { fontSize: 12, lineHeight: 18 }, input: { minHeight: 46, borderWidth: 1, borderRadius: 11, paddingHorizontal: 12, fontSize: 14 }, providerRow: { flexDirection: 'row', gap: 8 }, provider: { flex: 1, minHeight: 42, borderRadius: 11, alignItems: 'center', justifyContent: 'center' }, providerText: { fontWeight: '800' }, fieldRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10 }, fieldLabel: { flex: 1, fontSize: 13, fontWeight: '700' }, smallInput: { width: 100, minHeight: 42, borderWidth: 1, borderRadius: 10, paddingHorizontal: 10, textAlign: 'right' },
});
