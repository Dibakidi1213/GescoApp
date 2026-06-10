import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const ParentDashboard = () => {
  const [children, setChildren] = useState([]);
  const [selectedChild, setSelectedChild] = useState(null);
  const [details, setDetails] = useState(null);

  useEffect(() => {
    fetchChildren();
  }, []);

  const fetchChildren = async () => {
    const token = await AsyncStorage.getItem('access_token');
    const response = await fetch('https://api.school.com/api/parent/children', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    setChildren(data);
  };

  const fetchChildDetails = async (childId) => {
    const token = await AsyncStorage.getItem('access_token');
    const response = await fetch(`https://api.school.com/api/parent/child/${childId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();
    setDetails(data);
    setSelectedChild(childId);
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.header}>Mes Enfants</Text>
      {children.map(child => (
        <View key={child.id} style={styles.childCard} onTouchEnd={() => fetchChildDetails(child.id)}>
          <Text style={styles.childName}>{child.name}</Text>
          <Text style={styles.childClass}>{child.class}</Text>
        </View>
      ))}

      {details && (
        <View style={styles.detailsSection}>
          <Text style={styles.sectionTitle}>Notes Récentes</Text>
          {details.grades.map((g, i) => (
            <Text key={i}>{g.subject}: {g.value} ({g.period})</Text>
          ))}

          <Text style={styles.sectionTitle}>Présence</Text>
          {details.attendance.map((a, i) => (
            <Text key={i}>{a.date}: {a.status}</Text>
          ))}
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, padding: 15, backgroundColor: '#f8f9fa' },
  header: { fontSize: 24, fontWeight: 'bold', marginBottom: 20 },
  childCard: { padding: 15, backgroundColor: '#fff', borderRadius: 10, marginBottom: 10, elevation: 3 },
  childName: { fontSize: 18, fontWeight: '600' },
  detailsSection: { marginTop: 20, padding: 15, backgroundColor: '#fff', borderRadius: 10 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', marginTop: 15, borderBottomWidth: 1 }
});

export default ParentDashboard;
