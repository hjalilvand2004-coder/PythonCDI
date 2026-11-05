import React, { useState, useEffect, useContext } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, RefreshControl, Linking } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { AppContext } from '../../App';
import { getPool } from '../api';

export default function HomeScreen({ navigation }) {
  const { user } = useContext(AppContext);
  const [stats, setStats] = useState({ urgent: 0, pending: 0, claimed: 0, completed: 0 });
  const [refreshing, setRefreshing] = useState(false);

  const isAssistant = user?.uid && !['beneficiary', 'hqmanager', 'employ'].includes(user.uid);

  const loadData = async () => {
    setRefreshing(true);
    if (isAssistant) {
      const cases = await getPool();
      setStats({
        urgent: cases.filter(c => c.score >= 600 || c.flags?.length > 0).length,
        pending: cases.length,
        claimed: 0,
        completed: 0,
      });
    }
    setRefreshing(false);
  };

  useEffect(() => { loadData(); }, []);

  return (
    <View style={styles.container}>
      {/* Header */}
      <LinearGradient colors={['#1d3d63', '#162d4a']} style={styles.header}>
        <View style={styles.headerRow}>
          <View>
            <Text style={styles.headerTitle}>داشبورد</Text>
            <Text style={styles.headerSub}>{isAssistant ? 'حالت همیار' : 'حالت نیازمند'}</Text>
          </View>
          <TouchableOpacity onPress={() => navigation.replace('Login')}>
            <Ionicons name="log-out-outline" size={24} color="rgba(255,255,255,0.7)" />
          </TouchableOpacity>
        </View>
      </LinearGradient>

      <ScrollView
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={loadData} />}
        style={styles.content}
      >
        {/* Stats Grid */}
        {isAssistant ? (
          <View style={styles.statsGrid}>
            <StatCard num={stats.urgent} label="فوری" color="#dc2626" icon="alert-circle" />
            <StatCard num={stats.pending} label="در انتظار" color="#f59e0b" icon="time" />
            <StatCard num={stats.claimed} label="در رسیدگی" color="#1d3d63" icon="clipboard" />
            <StatCard num={stats.completed} label="تکمیل‌شده" color="#16a34a" icon="checkmark-done" />
          </View>
        ) : (
          <View style={styles.statsGrid}>
            <StatCard num="📝" label="ثبت‌نام" color="#12938d" icon="document-text" />
            <StatCard num="📋" label="وضعیت" color="#1d3d63" icon="list" />
          </View>
        )}

        {/* Quick Actions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>⚡ دسترسی سریع</Text>
          {isAssistant ? (
            <>
              <ActionButton title="🏊 استخر درخواست‌ها" icon="swap" onPress={() => navigation.navigate('Pool')} gradient={['#1d3d63', '#12938d']} />
              <ActionButton title="💰 کیف پول و عملکرد" icon="wallet" onPress={() => navigation.navigate('Wallet')} gradient={['#16a34a', '#15803d']} />
            </>
          ) : (
            <ActionButton title="📝 ثبت‌نام و پرسشنامه" icon="document-text" onPress={() => Linking.openURL('http://188.212.96.235:8085/questionnaire?action=register')} gradient={['#1d3d63', '#12938d']} />
          )}
        </View>
      </ScrollView>

      {/* Bottom Nav */}
      <BottomNav active="home" isAssistant={isAssistant} navigation={navigation} />
    </View>
  );
}

function StatCard({ num, label, color, icon }) {
  return (
    <View style={styles.statCard}>
      <Ionicons name={icon} size={20} color={color} style={styles.statIcon} />
      <Text style={[styles.statNum, { color }]}>{num}</Text>
      <Text style={styles.statLbl}>{label}</Text>
    </View>
  );
}

function ActionButton({ title, icon, onPress, gradient }) {
  return (
    <TouchableOpacity onPress={onPress} style={styles.actionBtn} activeOpacity={0.8}>
      <LinearGradient colors={gradient} style={styles.actionGradient}>
        <Ionicons name={icon} size={22} color="#fff" />
        <Text style={styles.actionText}>{title}</Text>
        <Ionicons name="chevron-back" size={20} color="rgba(255,255,255,0.5)" />
      </LinearGradient>
    </TouchableOpacity>
  );
}

function BottomNav({ active, isAssistant, navigation }) {
  const tabs = isAssistant ? [
    { id: 'pool', icon: 'swap', label: 'استخر', nav: 'Pool' },
    { id: 'home', icon: 'home', label: 'خانه', nav: 'Home' },
    { id: 'wallet', icon: 'wallet', label: 'کیف پول', nav: 'Wallet' },
  ] : [
    { id: 'home', icon: 'home', label: 'خانه', nav: 'Home' },
    { id: 'register', icon: 'document-text', label: 'پرسشنامه', nav: null },
  ];

  return (
    <View style={styles.bottomNav}>
      {tabs.map(tab => (
        <TouchableOpacity
          key={tab.id}
          style={styles.navTab}
          onPress={() => {
            if (tab.nav) navigation.navigate(tab.nav);
            else if (tab.id === 'register') Linking.openURL('http://188.212.96.235:8085/questionnaire?action=register');
          }}
        >
          <Ionicons name={tab.icon} size={22} color={active === tab.id ? '#1d3d63' : '#94a3b8'} />
          <Text style={[styles.navLabel, active === tab.id && styles.navLabelActive]}>{tab.label}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f4f7fa' },
  header: { paddingTop: 50, paddingBottom: 16, paddingHorizontal: 20 },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  headerTitle: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  headerSub: { color: 'rgba(255,255,255,0.6)', fontSize: 12, marginTop: 2 },
  content: { flex: 1, padding: 16 },
  statsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 20 },
  statCard: {
    flex: 1, minWidth: '45%', backgroundColor: '#fff', borderRadius: 14,
    padding: 14, alignItems: 'center', shadowColor: '#000', shadowOpacity: 0.05,
    shadowRadius: 8, elevation: 3,
  },
  statIcon: { marginBottom: 4 },
  statNum: { fontSize: 24, fontWeight: 'bold' },
  statLbl: { fontSize: 11, color: '#64748b', marginTop: 2 },
  section: { marginBottom: 16 },
  sectionTitle: { fontSize: 15, fontWeight: 'bold', color: '#1d3d63', marginBottom: 10 },
  actionBtn: { borderRadius: 12, overflow: 'hidden', marginBottom: 10 },
  actionGradient: {
    flexDirection: 'row', alignItems: 'center', padding: 16, gap: 10,
  },
  actionText: { flex: 1, color: '#fff', fontSize: 16, fontWeight: '600', marginLeft: 10 },
  bottomNav: {
    flexDirection: 'row', backgroundColor: '#fff', borderTopWidth: 1, borderTopColor: '#e2e8f0',
    paddingBottom: 20, paddingTop: 8,
  },
  navTab: { flex: 1, alignItems: 'center', gap: 2 },
  navLabel: { fontSize: 10, color: '#94a3b8' },
  navLabelActive: { color: '#1d3d63', fontWeight: '600' },
});
