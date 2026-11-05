import React, { useState } from 'react';
import { View, Text, TouchableOpacity, TextInput, StyleSheet, Alert, Linking } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { submitSatisfaction } from '../api';

const DIMENSIONS = [
  { id: 'behavior', label: 'نحوه برخورد', icon: '😊' },
  { id: 'expertise', label: 'تخصص و دانش', icon: '🎓' },
  { id: 'punctuality', label: 'وقت‌شناسی', icon: '⏰' },
  { id: 'followup', label: 'پیگیری', icon: '📋' },
  { id: 'respect', label: 'حریم خصوصی', icon: '🔒' },
];

export default function SatisfactionScreen({ route, navigation }) {
  const { hid } = route.params;
  const [scores, setScores] = useState({});
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const setScore = (dim, val) => setScores({ ...scores, [dim]: val });

  const handleSubmit = async () => {
    const count = Object.keys(scores).length;
    if (count < DIMENSIONS.length) {
      Alert.alert('خطا', 'لطفاً همه موارد را ارزیابی کنید');
      return;
    }
    setSubmitting(true);
    const ok = await submitSatisfaction(hid, scores, comment);
    setSubmitting(false);
    if (ok) {
      Alert.alert('✅ ثبت شد', 'از شما متشکریم!', [{ text: 'باشه', onPress: () => navigation.replace('Home') }]);
    } else {
      Alert.alert('خطا', 'ثبت ناموفق');
    }
  };

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#1d3d63', '#162d4a']} style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Ionicons name="chevron-forward" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>رضایت‌سنجی عملکرد همیار</Text>
      </LinearGradient>

      <View style={styles.content}>
        {DIMENSIONS.map(dim => (
          <View key={dim.id} style={styles.dimCard}>
            <Text style={styles.dimIcon}>{dim.icon}</Text>
            <Text style={styles.dimLabel}>{dim.label}</Text>
            <View style={styles.starsRow}>
              {[1, 2, 3, 4, 5].map(i => (
                <TouchableOpacity key={i} onPress={() => setScore(dim.id, i)}>
                  <Text style={[styles.star, scores[dim.id] >= i && styles.starActive]}>
                    {scores[dim.id] >= i ? '⭐' : '☆'}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        ))}

        <TextInput
          style={styles.comment}
          placeholder="💬 نظر شما (اختیاری)"
          value={comment}
          onChangeText={setComment}
          multiline
          textAlignVertical="top"
        />

        <TouchableOpacity onPress={handleSubmit} disabled={submitting} style={styles.submitBtn}>
          <LinearGradient colors={['#16a34a', '#15803d']} style={styles.submitGradient}>
            <Text style={styles.submitText}>{submitting ? '...' : '✅ ثبت رضایت‌سنجی'}</Text>
          </LinearGradient>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f4f7fa' },
  header: { paddingTop: 50, paddingBottom: 16, paddingHorizontal: 20, flexDirection: 'row', alignItems: 'center', gap: 12 },
  headerTitle: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  content: { padding: 16 },
  dimCard: { backgroundColor: '#fff', borderRadius: 14, padding: 16, marginBottom: 10, alignItems: 'center', elevation: 2 },
  dimIcon: { fontSize: 28 },
  dimLabel: { fontSize: 14, fontWeight: '600', color: '#1d3d63', marginVertical: 8 },
  starsRow: { flexDirection: 'row', gap: 4 },
  star: { fontSize: 32 },
  starActive: {},
  comment: {
    backgroundColor: '#fff', borderRadius: 12, padding: 12, fontSize: 14,
    minHeight: 80, marginBottom: 12, borderWidth: 1, borderColor: '#e2e8f0',
  },
  submitBtn: { borderRadius: 12, overflow: 'hidden' },
  submitGradient: { padding: 14, alignItems: 'center' },
  submitText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});
