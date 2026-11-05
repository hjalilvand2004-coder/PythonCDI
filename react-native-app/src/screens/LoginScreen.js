import React, { useState, useContext } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView, Linking, Alert } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { AppContext } from '../../App';
import { login } from '../api';

const ROLES = [
  { id: 'beneficiary', label: 'نیازمند', icon: 'person', color: '#12938d' },
  { id: 'tehran_ast1', label: 'مریم احمدی — همیار', icon: 'hand-left', color: '#1d3d63' },
  { id: 'tehran_worker', label: 'کارشناس غربالگری', icon: 'search', color: '#1d3d63' },
  { id: 'tehran_rose', label: 'رئیس استان', icon: 'ribbon', color: '#8b5cf6' },
  { id: 'hqmanager', label: 'مدیر ستاد', icon: 'stats-chart', color: '#dc2626' },
];

export default function LoginScreen({ navigation }) {
  const { setUser, server } = useContext(AppContext);
  const [selectedRole, setSelectedRole] = useState('');
  const [password, setPassword] = useState('1234');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');

  const handleLogin = async () => {
    if (!selectedRole) { Alert.alert('خطا', 'نقش را انتخاب کنید'); return; }
    setLoading(true);
    setStatus('در حال ورود...');
    const result = await login(selectedRole, password);
    setLoading(false);
    if (result.success) {
      setUser({ uid: selectedRole, role: selectedRole });
      navigation.replace('Home');
    } else {
      setStatus(result.error);
    }
  };

  const handleRegister = () => {
    Linking.openURL(`${server}/questionnaire?action=register`);
  };

  return (
    <LinearGradient colors={['#1d3d63', '#162d4a']} style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        {/* Logo */}
        <View style={styles.logoBox}>
          <LinearGradient colors={['#12938d', '#0f766e']} style={styles.logoCircle}>
            <Ionicons name="shield-checkmark" size={36} color="#fff" />
          </LinearGradient>
        </View>
        <Text style={styles.title}>سامانه CDI امداد</Text>
        <Text style={styles.subtitle}>شناسایی، احراز، توانمندسازی</Text>

        {/* Role Selection */}
        <View style={styles.card}>
          <Text style={styles.label}>انتخاب نقش</Text>
          {ROLES.map(r => (
            <TouchableOpacity
              key={r.id}
              style={[styles.roleBtn, selectedRole === r.id && styles.roleBtnActive]}
              onPress={() => setSelectedRole(r.id)}
            >
              <Ionicons name={r.icon} size={20} color={selectedRole === r.id ? '#fff' : r.color} />
              <Text style={[styles.roleText, selectedRole === r.id && styles.roleTextActive]}>{r.label}</Text>
              {selectedRole === r.id && <Ionicons name="checkmark-circle" size={20} color="#fff" />}
            </TouchableOpacity>
          ))}

          <Text style={styles.label}>رمز عبور</Text>
          <TextInput
            style={styles.input}
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            placeholderTextColor="#94a3b8"
          />

          {status ? <Text style={styles.status}>{status}</Text> : null}

          <TouchableOpacity onPress={handleLogin} disabled={loading} style={styles.loginBtn}>
            <LinearGradient colors={['#1d3d63', '#12938d']} style={styles.loginGradient}>
              <Ionicons name="log-in" size={20} color="#fff" />
              <Text style={styles.loginText}>{loading ? '...' : 'ورود'}</Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>

        {/* Register */}
        <TouchableOpacity onPress={handleRegister} style={styles.registerBtn}>
          <Ionicons name="person-add" size={20} color="#12938d" />
          <Text style={styles.registerText}>ثبت‌نام نیازمند جدید</Text>
        </TouchableOpacity>
      </ScrollView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scroll: { alignItems: 'center', padding: 24, paddingTop: 60 },
  logoBox: { marginBottom: 12 },
  logoCircle: { width: 72, height: 72, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  title: { color: '#fff', fontSize: 22, fontWeight: 'bold' },
  subtitle: { color: 'rgba(255,255,255,0.6)', fontSize: 13, marginTop: 4 },
  card: { width: '100%', backgroundColor: '#fff', borderRadius: 16, padding: 20, marginTop: 24 },
  label: { fontSize: 13, fontWeight: '600', color: '#334155', marginBottom: 8, marginTop: 12 },
  roleBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    padding: 12, borderRadius: 10, borderWidth: 1.5, borderColor: '#e2e8f0',
    marginBottom: 6,
  },
  roleBtnActive: { backgroundColor: '#1d3d63', borderColor: '#1d3d63' },
  roleText: { flex: 1, fontSize: 14, color: '#1a2b3c', marginLeft: 8 },
  roleTextActive: { color: '#fff' },
  input: {
    borderWidth: 1.5, borderColor: '#e2e8f0', borderRadius: 10,
    padding: 12, fontSize: 16, color: '#1a2b3c',
  },
  status: { color: '#dc2626', fontSize: 12, marginTop: 8, textAlign: 'center' },
  loginBtn: { marginTop: 16, borderRadius: 12, overflow: 'hidden' },
  loginGradient: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    padding: 14, gap: 8,
  },
  loginText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  registerBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: 8, marginTop: 16, padding: 14, borderWidth: 2, borderColor: '#12938d',
    borderRadius: 12, width: '100%',
  },
  registerText: { color: '#12938d', fontSize: 15, fontWeight: '600' },
});
