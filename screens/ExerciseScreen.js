import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const ExerciseScreen = ({ navigation, route }) => {
    const { exerciseName } = route.params;
  
    const user = {
      name: 'John Doe',
      points: 1450,
      deviceStatus: 'Connected',
      energySaved: '34.7 kWh',
      lastSynced: 'April 20, 2025, 14:32',
    };
  
    return (
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>{exerciseName}</Text>
  
        <View style={styles.card}>
          <Text style={styles.label}>User:</Text>
          <Text style={styles.value}>{user.name}</Text>
        </View>
  
        <View style={styles.card}>
          <Text style={styles.label}>Total Points</Text>
          <Text style={styles.points}>{user.points} pts</Text>
        </View>
  
        <View style={styles.card}>
          <Text style={styles.label}>Device Status</Text>
          <Text style={[styles.value, { color: user.deviceStatus === 'Connected' ? '#4caf50' : '#f44336' }]}>
            {user.deviceStatus}
          </Text>
        </View>
  
        <View style={styles.card}>
          <Text style={styles.label}>Energy Saved</Text>
          <Text style={styles.value}>{user.energySaved}</Text>
        </View>
  
        <View style={styles.card}>
          <Text style={styles.label}>Last Synced</Text>
          <Text style={styles.value}>{user.lastSynced}</Text>
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
    },
    label: {
      fontSize: 16,
      color: '#888',
      marginBottom: 4,
    },
    value: {
      fontSize: 18,
      fontWeight: '600',
      color: '#333',
    },
    points: {
      fontSize: 22,
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
