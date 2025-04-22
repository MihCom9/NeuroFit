import React, { useEffect, useRef, useCallback, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';

const ExerciseScreen = ({ navigation, route }) => {
  const { exerciseName } = route.params;
  const hasSentOnce = useRef(false);
  const [latestScore, setLatestScore] = useState(null);

  useFocusEffect(
    useCallback(() => {
      hasSentOnce.current = false;
    }, [])
  );

  useEffect(() => {
    if (!hasSentOnce.current) {
      hasSentOnce.current = true;

      fetch('http://172.20.10.8:8080/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exercise: exerciseName }),
      })
        .then(res => res.json())
        .then(data => {
          console.log('✅ Exercise started:', data);
        })
        .catch(err => {
          console.error('❌ Failed to start exercise:', err);
        });
    }

    const interval = setInterval(() => {
      fetch('http://172.20.10.8:8080/data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          acceleration_x: Math.random() * 2,
          acceleration_y: Math.random() * 2,
          acceleration_z: Math.random() * 2,
          altitude: Math.random() * 10,
        }),
      })
        .then(res => res.json())
        .then(data => {
          if (typeof data.score === 'number') {
            setLatestScore(data.score); // Update the latestScore with the received score
          }
        })
        .catch(err => console.error('Fetch error:', err));
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [exerciseName]);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>{exerciseName}</Text>

      <View style={styles.card}>
        <Text style={styles.label}>Latest Score:</Text>
        <Text style={styles.points}>
          {latestScore !== null ? `${latestScore} pts` : 'Waiting for score...'}
        </Text>
      </View>

      <TouchableOpacity style={styles.button} onPress={() => navigation.goBack()}>
        <Ionicons name="arrow-back-outline" size={20} color="#fff" />
        <Text style={styles.buttonText}>Back</Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingVertical: 30,
    paddingHorizontal: 20,
    backgroundColor: '#f0f4f8',
    flexGrow: 1,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 25,
    color: '#333',
  },
  card: {
    backgroundColor: '#fff',
    padding: 18,
    borderRadius: 14,
    marginBottom: 15,
    elevation: 3,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
    alignItems: 'center',
  },
  label: {
    fontSize: 18,
    color: '#888',
    marginBottom: 8,
  },
  points: {
    fontSize: 30,
    fontWeight: 'bold',
    color: '#007bff',
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#007bff',
    padding: 14,
    borderRadius: 12,
    justifyContent: 'center',
    marginTop: 30,
  },
  buttonText: {
    color: '#fff',
    marginLeft: 10,
    fontSize: 16,
    fontWeight: '600',
  },
});

export default ExerciseScreen;
